"""Implementations of the verification MCP tools.

Exposes ``*_impl`` async entrypoints called from ``LASSI_mcp.py``:

- ``build_sanitized_impl`` — compile C/C++ with strict warnings and sanitizers.
- ``synthesize_common_harness_impl`` — emits a Python/ctypes harness shared
  between two implementations.
- ``generate_assertion_suite_impl`` — generates the assertion test script.
- ``run_assertion_suite_impl`` — runs the generated assertion suite against
  two artifacts.
- ``run_random_equivalence_tests_impl`` — randomized differential testing.
- ``run_robustness_fuzzer_impl`` — libFuzzer with sanitizer instrumentation.
- ``run_differential_fuzzer_impl`` — differential libFuzzer comparing two
  implementations.
- ``synthesize_verification_report_impl`` — aggregates verification verdicts
  into ``.verify/reports/*.json`` and ``.md``.

Also exposes ``random_equivalence_main`` which is invoked by the generated
``test_equivalence.py`` harnesses under ``.verify/harnesses/*``.

Shared helpers come from :mod:`lassi.core.mcp_helpers`,
:mod:`lassi.core.command`, and :mod:`lassi.core.responses`. Verdict shape
(``VALID_VERDICTS``) remains local to this module.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import math
import os
import pickle
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path
from typing import Any

import numpy as np

from lassi.core.mcp_helpers import now_task_id as _now_task_id
from lassi.core.mcp_helpers import short as _short
from lassi.core.mcp_helpers import write_json as _write_json
from lassi.core.command import run_command as _shared_run_command
from lassi.core.responses import json_response as _shared_json_response


VALID_VERDICTS = {"PASS", "FAIL", "UNSURE", "ERROR"}
VERIFY_ROOT = Path(".verify")


def _json_response(
    verdict: str,
    confidence: float,
    summary: str,
    *,
    artifacts: list[dict[str, Any]] | None = None,
    counterexamples: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
    logs: dict[str, str] | None = None,
) -> str:
    return _shared_json_response(
        verdict,
        confidence,
        summary,
        valid_verdicts=VALID_VERDICTS,
        invalid_summary_prefix="Internal error: invalid verdict emitted.",
        artifacts=artifacts,
        counterexamples=counterexamples or [],
        metrics=metrics,
        logs=logs,
    )


def _loads_result(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def _resolve_verify_root(base_dir: str | None = None) -> Path:
    root = Path(base_dir).resolve() if base_dir else (Path.cwd() / VERIFY_ROOT).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run_command(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout_s: int | float = 60,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return _shared_run_command(
        cmd,
        cwd=cwd,
        env=env,
        timeout_s=timeout_s,
        merge_env=False,
    )


def _sanitize_token(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:10]
    return f"{path.stem}_{digest}"


def _discover_sources(source_path: Path, language: str) -> tuple[list[Path], str]:
    if source_path.is_file():
        files = [source_path.resolve()]
    elif source_path.is_dir():
        suffixes = {".c", ".cc", ".cpp", ".cxx"}
        files = sorted(
            p.resolve()
            for p in source_path.rglob("*")
            if p.suffix.lower() in suffixes and ".verify" not in p.parts
        )
    else:
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    if not files:
        raise ValueError(f"No C/C++ source files found under {source_path}")

    lowered = language.lower()
    if lowered == "auto":
        inferred = "cpp" if any(p.suffix.lower() in {".cc", ".cpp", ".cxx"} for p in files) else "c"
    elif lowered in {"c", "cpp"}:
        inferred = lowered
    else:
        raise ValueError("language must be one of: c, cpp, auto")

    return files, inferred


def _source_has_main(files: list[Path]) -> bool:
    pattern = re.compile(r"\bmain\s*\(")
    for path in files:
        try:
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            continue
    return False


def _sanitize_flag(sanitizers: list[str]) -> str:
    mapping = {
        "address": "address",
        "undefined": "undefined",
        "leak": "leak",
        "memory": "memory",
        "thread": "thread",
        "fuzzer": "fuzzer",
    }
    selected = []
    for sanitizer in sanitizers:
        key = str(sanitizer).lower().strip()
        if key in mapping and mapping[key] not in selected:
            selected.append(mapping[key])
    return f"-fsanitize={','.join(selected)}" if selected else ""


def _default_flags(warnings_as_errors: bool) -> list[str]:
    flags = ["-Wall", "-Wextra", "-Wpedantic", "-g", "-fno-omit-frame-pointer"]
    if warnings_as_errors:
        flags.append("-Werror")
    return flags


def _compile_sources(
    files: list[Path],
    compiler: str,
    build_dir: Path,
    output_name: str,
    build_mode: str,
    opt_level: str,
    sanitizers: list[str],
    warnings_as_errors: bool,
    timeout_s: int,
    extra_compile_flags: list[str],
    extra_link_flags: list[str],
) -> tuple[list[dict[str, str]], subprocess.CompletedProcess[str]]:
    build_dir.mkdir(parents=True, exist_ok=True)
    opt_flag = opt_level if opt_level.startswith("-") else f"-{opt_level}"
    common_flags = [opt_flag, *_default_flags(warnings_as_errors), *extra_compile_flags]
    sanitize = _sanitize_flag(sanitizers)
    if sanitize:
        common_flags.append(sanitize)

    if build_mode == "object":
        artifacts = []
        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        returncode = 0
        for source in files:
            out = build_dir / f"{source.stem}_{opt_level}.o"
            cmd = [compiler, "-c", str(source), *common_flags, "-o", str(out)]
            proc = _run_command(cmd, timeout_s=timeout_s)
            stdout_parts.append(f"$ {' '.join(cmd)}\n{proc.stdout}")
            stderr_parts.append(proc.stderr)
            returncode = proc.returncode if proc.returncode != 0 else returncode
            if proc.returncode == 0:
                artifacts.append({"kind": "object", "path": str(out)})
        merged = subprocess.CompletedProcess(
            args=["object-build"],
            returncode=returncode,
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
        )
        return artifacts, merged

    out_suffix = ".so" if build_mode == "shared_library" else ""
    out = build_dir / f"{output_name}_{opt_level}{out_suffix}"
    mode_flags = ["-shared", "-fPIC"] if build_mode == "shared_library" else []
    cmd = [
        compiler,
        *[str(p) for p in files],
        *common_flags,
        *mode_flags,
        *extra_link_flags,
        "-o",
        str(out),
    ]
    proc = _run_command(cmd, timeout_s=timeout_s)
    kind = "shared_library" if build_mode == "shared_library" else "binary"
    artifacts = [{"kind": kind, "path": str(out)}] if proc.returncode == 0 else []
    proc.stdout = f"$ {' '.join(cmd)}\n{proc.stdout}"
    return artifacts, proc


async def build_sanitized_impl(
    source_path: str,
    language: str = "auto",
    entrypoint_hint: str | None = None,
    build_mode: str = "auto",
    optimization_levels: list[str] | None = None,
    sanitizers: list[str] | None = None,
    warnings_as_errors: bool = True,
    timeout_s: int = 60,
    extra_compile_flags: list[str] | None = None,
    extra_link_flags: list[str] | None = None,
) -> str:
    del entrypoint_hint
    if optimization_levels is None:
        optimization_levels = ["O0", "O1", "O2", "O3"]
    if sanitizers is None:
        sanitizers = ["address", "undefined"]
    if extra_compile_flags is None:
        extra_compile_flags = []
    if extra_link_flags is None:
        extra_link_flags = []
    source = Path(source_path).resolve()

    try:
        files, inferred_language = _discover_sources(source, language)
    except Exception as exc:
        return _json_response("ERROR", 0.0, str(exc))

    compiler = "clang++" if inferred_language == "cpp" else "clang"
    if shutil.which(compiler) is None:
        return _json_response(
            "ERROR",
            0.0,
            f"Required compiler not found: {compiler}",
            metrics={"compiler": compiler},
        )

    mode = build_mode.lower()
    if mode == "auto":
        mode = "binary" if _source_has_main(files) else "shared_library"
    if mode not in {"binary", "shared_library", "object"}:
        return _json_response("ERROR", 0.0, "build_mode must be binary, shared_library, object, or auto")

    root = _resolve_verify_root()
    build_root = root / "builds" / _sanitize_token(source)
    artifacts: list[dict[str, str]] = []
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    builds_attempted = 0
    builds_succeeded = 0
    failed_command: str | None = None
    timeout_seen = False

    for opt in optimization_levels:
        builds_attempted += 1
        try:
            produced, proc = _compile_sources(
                files,
                compiler,
                build_root / opt,
                source.stem if source.is_file() else source.name,
                mode,
                opt,
                sanitizers,
                warnings_as_errors,
                int(timeout_s),
                extra_compile_flags,
                extra_link_flags,
            )
        except subprocess.TimeoutExpired as exc:
            timeout_seen = True
            stdout_parts.append(exc.stdout or "")
            stderr_parts.append(exc.stderr or f"Timed out after {timeout_s}s")
            failed_command = " ".join(str(x) for x in exc.cmd) if exc.cmd else None
            break
        except Exception as exc:
            return _json_response("ERROR", 0.0, f"Build infrastructure error: {exc}")

        stdout_parts.append(proc.stdout or "")
        stderr_parts.append(proc.stderr or "")
        if proc.returncode != 0:
            failed_command = " ".join(str(x) for x in proc.args) if isinstance(proc.args, list) else str(proc.args)
            break
        builds_succeeded += 1
        artifacts.extend(produced)

        for artifact in produced:
            if artifact["kind"] != "binary":
                continue
            try:
                smoke = _run_command([artifact["path"]], timeout_s=min(int(timeout_s), 10))
            except subprocess.TimeoutExpired as exc:
                return _json_response(
                    "FAIL",
                    0.15,
                    "Sanitized binary smoke run timed out.",
                    artifacts=artifacts,
                    counterexamples=[{"kind": "timeout", "reproducer_command": artifact["path"]}],
                    metrics={"builds_attempted": builds_attempted, "builds_succeeded": builds_succeeded},
                    logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
                )
            stdout_parts.append(smoke.stdout or "")
            stderr_parts.append(smoke.stderr or "")
            if smoke.returncode != 0:
                return _json_response(
                    "FAIL",
                    0.2,
                    "Sanitized binary crashed or returned non-zero during smoke run.",
                    artifacts=artifacts,
                    counterexamples=[{"kind": "smoke_run_failure", "reproducer_command": artifact["path"]}],
                    metrics={"builds_attempted": builds_attempted, "builds_succeeded": builds_succeeded},
                    logs={"stdout": _short("\n".join(stdout_parts)), "stderr": _short("\n".join(stderr_parts))},
                )

    stderr_text = "\n".join(stderr_parts)
    warning_count = len(re.findall(r"\bwarning:", stderr_text, flags=re.IGNORECASE))
    logs = {"stdout": _short("\n".join(stdout_parts)), "stderr": _short(stderr_text)}

    if timeout_seen:
        return _json_response(
            "ERROR",
            0.0,
            "Sanitizer build timed out.",
            artifacts=artifacts,
            metrics={"builds_attempted": builds_attempted, "builds_succeeded": builds_succeeded, "warnings": warning_count},
            logs=logs,
        )

    if builds_succeeded != builds_attempted:
        return _json_response(
            "FAIL",
            0.2,
            "Sanitizer build failed.",
            artifacts=artifacts,
            counterexamples=[{"kind": "compile_failure", "reproducer_command": failed_command}],
            metrics={"builds_attempted": builds_attempted, "builds_succeeded": builds_succeeded, "warnings": warning_count},
            logs=logs,
        )

    return _json_response(
        "PASS",
        0.9,
        "All sanitizer builds succeeded.",
        artifacts=artifacts,
        metrics={
            "builds_attempted": builds_attempted,
            "builds_succeeded": builds_succeeded,
            "warnings": warning_count,
            "compiler": compiler,
            "build_mode": mode,
            "optimization_levels": optimization_levels,
            "sanitizers": sanitizers,
        },
        logs=logs,
    )


_HARNESS_TEMPLATE = r'''
from __future__ import annotations

import ctypes
import importlib.util
import math
import re
import subprocess
from pathlib import Path

import numpy as np

try:
    import torch
except Exception:
    torch = None


_NUMBER_RE = re.compile(r"[\-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][\-+]?\d+)?")


def _load_python_callable(path, entrypoint):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    fn = getattr(module, entrypoint)
    return fn


def _ctype(name):
    return {
        "double": ctypes.c_double,
        "float": ctypes.c_float,
        "int": ctypes.c_int,
        "long": ctypes.c_long,
    }[name]


def _parse_signature(signature):
    signature = signature or "double(double)"
    ret, args = signature.split("(", 1)
    args = args.rstrip(")")
    return ret.strip(), [arg.strip() for arg in args.split(",") if arg.strip()]


def _load_shared_scalar(path, entrypoint, signature):
    ret, args = _parse_signature(signature)
    lib = ctypes.CDLL(path)
    fn = getattr(lib, entrypoint)
    fn.restype = _ctype(ret)
    fn.argtypes = [_ctype(arg) for arg in args]
    return fn


def _parse_number_from_stdout(stdout):
    for line in reversed(stdout.splitlines()):
        for token in line.split():
            if "=" in token:
                val = token.rsplit("=", 1)[1]
                m = _NUMBER_RE.fullmatch(val)
                if m:
                    return float(m.group(0))
        for token in line.split():
            m = _NUMBER_RE.fullmatch(token)
            if m:
                return float(m.group(0))
    raise RuntimeError(f"binary produced no numeric stdout token:\n{stdout!r}")


def _load_binary_subprocess(path):
    path = str(path)

    def fn(case):
        cmd = [path]
        if isinstance(case, (list, tuple)):
            cmd.extend(str(c) for c in case)
        else:
            cmd.append(str(case))
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
        if proc.returncode != 0:
            raise RuntimeError(
                f"binary {path} exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
            )
        return _parse_number_from_stdout(proc.stdout)

    return fn


def _load_callable(path, entrypoint, signature=None):
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return _load_python_callable(path, entrypoint)
    if suffix in {".so", ".dylib", ".dll"}:
        return _load_shared_scalar(path, entrypoint, signature)
    return _load_binary_subprocess(path)


def _call(fn, input_case):
    if isinstance(input_case, (list, tuple)):
        return fn(*input_case)
    return fn(input_case)


def _to_numpy(value):
    if torch is not None and hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def run_a(input_case):
    return _call(_IMPL_A, input_case)


def run_b(input_case):
    return _call(_IMPL_B, input_case)


def compare_outputs(a_out, b_out, *, rtol=1e-5, atol=1e-6, mode="allclose"):
    a_np = _to_numpy(a_out)
    b_np = _to_numpy(b_out)
    if mode == "exact":
        return bool(np.array_equal(a_np, b_np))
    return bool(np.allclose(a_np, b_np, rtol=rtol, atol=atol, equal_nan=True))


_IMPL_A = None
_IMPL_B = None


def configure(implementation_a, implementation_b, entrypoint="kernel", signature="double(double)"):
    global _IMPL_A, _IMPL_B
    _IMPL_A = _load_callable(implementation_a, entrypoint, signature)
    _IMPL_B = _load_callable(implementation_b, entrypoint, signature)
'''


async def synthesize_common_harness_impl(
    source_a: str,
    source_b: str,
    task_type: str,
    entrypoints: list[dict[str, Any]] | None = None,
    input_schema: Any = "auto",
    output_schema: Any = "auto",
) -> str:
    del input_schema, output_schema
    root = _resolve_verify_root()
    task_id = _now_task_id("harness")
    out_dir = root / "harnesses" / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    harness_path = out_dir / "common_harness.py"
    metadata_path = out_dir / "harness_metadata.json"
    entrypoint = (entrypoints or [{"name": "kernel"}])[0]
    harness_path.write_text(_HARNESS_TEMPLATE, encoding="utf-8")
    metadata = {
        "source_a": str(Path(source_a).resolve()),
        "source_b": str(Path(source_b).resolve()),
        "task_type": task_type,
        "entrypoints": entrypoints or [],
        "supported_interfaces": ["python_module_callable", "ctypes_scalar_shared_library"],
    }
    _write_json(metadata_path, metadata)
    confidence = 0.7 if entrypoint.get("signature") else 0.55
    return _json_response(
        "PASS",
        confidence,
        "Synthesized common Python harness for Python callables and scalar ctypes shared libraries.",
        artifacts=[
            {"kind": "python_harness", "path": str(harness_path)},
            {"kind": "metadata", "path": str(metadata_path)},
        ],
        metrics={"entrypoints_found": len(entrypoints or []), "primary_entrypoint": entrypoint.get("name", "kernel")},
    )


def _assertion_suite_source(
    entrypoint: str,
    signature: str,
    rtol: float,
    atol: float,
) -> str:
    return f'''from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HARNESS_PATH = os.environ.get("LASSI_HARNESS_PATH")
if HARNESS_PATH:
    sys.path.insert(0, str(Path(HARNESS_PATH).resolve().parent))
    import common_harness as harness
else:
    raise RuntimeError("LASSI_HARNESS_PATH is required")

ENTRYPOINT = {entrypoint!r}
SIGNATURE = {signature!r}
RTOL = {rtol!r}
ATOL = {atol!r}
ASSERTION_CASES = [-2.0, -1.0, -0.0, 0.0, 1.0, 2.0, 16.0]


def _finite(value):
    arr = harness._to_numpy(value)
    return bool(np.isfinite(arr).all())


def main():
    impl_a = os.environ["IMPLEMENTATION_A_ARTIFACT"]
    impl_b = os.environ["IMPLEMENTATION_B_ARTIFACT"]
    harness.configure(impl_a, impl_b, ENTRYPOINT, SIGNATURE)
    failures = []
    assertions_run = 0
    for case in ASSERTION_CASES:
        a_out = harness.run_a(case)
        b_out = harness.run_b(case)
        assertions_run += 3
        if not _finite(a_out):
            failures.append({{"input": case, "assertion": "implementation A output is finite", "a_result": "FAIL", "b_result": "NOT_RUN"}})
        if not _finite(b_out):
            failures.append({{"input": case, "assertion": "implementation B output is finite", "a_result": "PASS", "b_result": "FAIL"}})
        if not harness.compare_outputs(a_out, b_out, rtol=RTOL, atol=ATOL, mode="allclose"):
            failures.append({{"input": case, "assertion": "A and B outputs are allclose", "a_output": str(a_out), "b_output": str(b_out)}})
    result = {{
        "assertions_run": assertions_run,
        "failures": failures,
        "a_failures": sum(1 for f in failures if f.get("a_result") == "FAIL"),
        "b_failures": sum(1 for f in failures if f.get("b_result") == "FAIL"),
    }}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


async def generate_assertion_suite_impl(
    source_a: str,
    source_b: str,
    task_type: str,
    entrypoints: list[dict[str, Any]] | None = None,
    existing_tests: list[str] | None = None,
    semantic_hints: list[str] | None = None,
    numeric_tolerance: dict[str, float] | None = None,
    timeout_s: int = 120,
) -> str:
    del semantic_hints, timeout_s
    tolerance = numeric_tolerance or {"rtol": 1e-5, "atol": 1e-6}
    entrypoint = (entrypoints or [{"name": "kernel", "signature": "double(double)"}])[0]
    root = _resolve_verify_root()
    task_id = _now_task_id("assertions")
    out_dir = root / "assertions" / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    harness_result = _loads_result(await synthesize_common_harness_impl(
        source_a=str(source_a),
        source_b=str(source_b),
        task_type=task_type,
        entrypoints=entrypoints or [entrypoint],
    ))
    harness_path = next((a["path"] for a in harness_result["artifacts"] if a["kind"] == "python_harness"), "")
    suite_path = out_dir / "assertion_suite.py"
    suite_path.write_text(
        _assertion_suite_source(
            entrypoint.get("name", "kernel"),
            entrypoint.get("signature", "double(double)"),
            float(tolerance.get("rtol", 1e-5)),
            float(tolerance.get("atol", 1e-6)),
        ),
        encoding="utf-8",
    )
    manifest_path = out_dir / "assertion_manifest.json"
    manifest = {
        "assertion_suite": str(suite_path),
        "harness": harness_path,
        "entrypoint": entrypoint,
        "existing_tests": existing_tests or [],
        "numeric_tolerance": tolerance,
    }
    _write_json(manifest_path, manifest)
    generated = 3 * 7
    from_source = len(existing_tests or [])
    return _json_response(
        "PASS",
        0.6 if from_source == 0 else 0.7,
        f"Generated {generated} shared assertion checks over smoke inputs.",
        artifacts=[
            {"kind": "assertion_suite", "path": str(suite_path)},
            {"kind": "python_harness", "path": harness_path},
            {"kind": "manifest", "path": str(manifest_path)},
        ],
        metrics={
            "assertions_generated": generated,
            "assertions_from_source": from_source,
            "metamorphic_assertions": 0,
        },
    )


async def run_assertion_suite_impl(
    assertion_suite_path: str,
    implementation_a_artifact: str,
    implementation_b_artifact: str,
    task_type: str,
    timeout_s: int = 120,
) -> str:
    del task_type
    suite = Path(assertion_suite_path).resolve()
    if not suite.exists():
        return _json_response("ERROR", 0.0, f"Assertion suite not found: {suite}")
    impl_a = Path(implementation_a_artifact).resolve()
    impl_b = Path(implementation_b_artifact).resolve()
    if not impl_a.exists() or not impl_b.exists():
        return _json_response("ERROR", 0.0, "Both implementation artifacts must exist.")

    harness_path = suite.parent / "common_harness.py"
    manifest = suite.parent / "assertion_manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            harness_path = Path(data.get("harness", harness_path)).resolve()
        except Exception:
            pass
    if not harness_path.exists():
        return _json_response("ERROR", 0.0, f"Common harness not found: {harness_path}")

    env = os.environ.copy()
    env.update({
        "LASSI_HARNESS_PATH": str(harness_path),
        "IMPLEMENTATION_A_ARTIFACT": str(impl_a),
        "IMPLEMENTATION_B_ARTIFACT": str(impl_b),
    })
    try:
        proc = _run_command([sys.executable, str(suite)], timeout_s=timeout_s, env=env)
    except subprocess.TimeoutExpired as exc:
        return _json_response(
            "UNSURE",
            0.2,
            "Assertion suite timed out.",
            logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
        )

    metrics: dict[str, Any] = {}
    counterexamples: list[dict[str, Any]] = []
    try:
        metrics = json.loads(proc.stdout)
        counterexamples = metrics.get("failures", [])
    except Exception:
        pass
    if proc.returncode == 0:
        verdict, confidence, summary = "PASS", 0.75, "Shared assertion suite passed for both implementations."
    else:
        verdict, confidence, summary = "FAIL", 0.95, "Shared assertion suite found a failure."
    return _json_response(
        verdict,
        confidence,
        summary,
        artifacts=[{"kind": "assertion_suite", "path": str(suite)}, {"kind": "python_harness", "path": str(harness_path)}],
        counterexamples=counterexamples,
        metrics=metrics,
        logs={"stdout": _short(proc.stdout), "stderr": _short(proc.stderr)},
    )


def _load_python_callable(path: str, entrypoint: str):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot import Python module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, entrypoint):
        return getattr(module, entrypoint)
    if hasattr(module, "model") and callable(getattr(module, "model")):
        return getattr(module, "model")
    raise AttributeError(f"Entrypoint {entrypoint!r} not found in {path}")


_SCALAR_CTYPES = {
    "double": ctypes.c_double,
    "float": ctypes.c_float,
    "int": ctypes.c_int,
    "long": ctypes.c_long,
    "void": None,
}

_POINTER_BASE_DTYPE = {
    "double": np.float64,
    "float": np.float32,
    "int": np.int32,
    "long": np.int64,
}


def _parse_arg_token(token: str) -> dict[str, Any]:
    """Parse a single C-ish argument token into a structured spec.

    Recognises: optional `const`, base scalar type, optional `*` for pointer,
    optional identifier name. Examples:
      "double"                -> {kind: scalar, base: double, ctype: c_double}
      "int n"                 -> {kind: scalar, base: int, name: "n", ctype: c_int}
      "double*"               -> {kind: pointer, base: double, const: False}
      "const double* A"       -> {kind: pointer, base: double, const: True, name: "A"}
    """
    raw = token.strip()
    is_const = False
    if raw.startswith("const "):
        is_const = True
        raw = raw[len("const "):].strip()
    parts = raw.split()
    if not parts:
        raise ValueError(f"Empty argument token in signature")
    name: str | None = None
    last = parts[-1]
    if last.isidentifier() and last not in _SCALAR_CTYPES:
        name = last
        parts = parts[:-1]
    type_text = " ".join(parts).replace(" ", "")
    is_pointer = type_text.endswith("*")
    if is_pointer:
        base = type_text.rstrip("*")
    else:
        base = type_text
    if base not in _SCALAR_CTYPES or base == "void":
        if not (base == "void" and is_pointer is False and name is None):
            raise ValueError(f"Unsupported argument base type: {base!r} in token {token!r}")
    if is_pointer:
        if base not in _POINTER_BASE_DTYPE:
            raise ValueError(f"Pointer base type not supported: {base!r}")
        return {
            "kind": "pointer",
            "base": base,
            "const": is_const,
            "name": name,
            "ctype": ctypes.POINTER(_SCALAR_CTYPES[base]),
            "numpy_dtype": _POINTER_BASE_DTYPE[base],
        }
    return {
        "kind": "scalar",
        "base": base,
        "name": name,
        "ctype": _SCALAR_CTYPES[base],
    }


def _parse_ctypes_signature(signature: str | None) -> tuple[Any, list[Any]]:
    """Backwards-compatible scalar-only parser (kept for the in-template harness)."""
    signature = signature or "double(double)"
    match = re.fullmatch(r"\s*(\w+)\s*\((.*?)\)\s*", signature)
    if not match:
        raise ValueError(f"Unsupported signature format: {signature}")
    ret_name, args_text = match.groups()
    arg_names = [part.strip() for part in args_text.split(",") if part.strip()]
    if ret_name not in _SCALAR_CTYPES or any(arg not in _SCALAR_CTYPES for arg in arg_names):
        raise ValueError(f"Only scalar ctypes signatures are supported initially: {signature}")
    return _SCALAR_CTYPES[ret_name], [_SCALAR_CTYPES[arg] for arg in arg_names]


def _parse_extended_signature(signature: str | None) -> dict[str, Any]:
    """Parse a signature that may contain pointer and named args.

    Returns: {return: {base, ctype, is_pointer}, args: [arg_spec, ...]}
    """
    signature = signature or "double(double)"
    match = re.fullmatch(r"\s*([\w\s\*]+?)\s*\((.*?)\)\s*", signature)
    if not match:
        raise ValueError(f"Unsupported signature format: {signature}")
    ret_text, args_text = match.groups()
    ret_text = ret_text.strip()
    ret_pointer = ret_text.endswith("*")
    ret_base = ret_text.rstrip("*").strip()
    if ret_base not in _SCALAR_CTYPES:
        raise ValueError(f"Unsupported return base type: {ret_base!r}")
    ret_ctype = (
        ctypes.POINTER(_SCALAR_CTYPES[ret_base])
        if ret_pointer and ret_base != "void"
        else _SCALAR_CTYPES[ret_base]
    )
    arg_specs = [_parse_arg_token(part) for part in args_text.split(",") if part.strip()]
    return {
        "return": {"base": ret_base, "ctype": ret_ctype, "is_pointer": ret_pointer},
        "args": arg_specs,
    }


def _is_pointer_signature(signature: str | None) -> bool:
    if not signature:
        return False
    return "*" in signature


def _load_callable(path: str, entrypoint: str, signature: str | None):
    suffix = Path(path).suffix
    if suffix == ".py":
        return _load_python_callable(path, entrypoint), "python"
    if suffix in {".so", ".dylib", ".dll"}:
        lib = ctypes.CDLL(path)
        fn = getattr(lib, entrypoint)
        if _is_pointer_signature(signature):
            parsed = _parse_extended_signature(signature)
            fn.restype = parsed["return"]["ctype"]
            fn.argtypes = [spec["ctype"] for spec in parsed["args"]]
            return (fn, parsed), "ctypes_pointer"
        restype, argtypes = _parse_ctypes_signature(signature)
        fn.restype = restype
        fn.argtypes = argtypes
        return fn, "ctypes_scalar"
    raise ValueError(f"Unsupported artifact type for random equivalence: {path}")


def _call_loaded(fn: Any, kind: str, case: Any) -> Any:
    if kind == "ctypes_scalar":
        if isinstance(case, tuple):
            return fn(*case)
        return fn(case)
    if kind == "ctypes_pointer":
        actual_fn, parsed = fn
        if not isinstance(case, dict):
            raise TypeError("ctypes_pointer cases must be dicts {arg_name: value}")
        call_args = []
        outputs: dict[str, np.ndarray] = {}
        for spec in parsed["args"]:
            name = spec.get("name")
            if name is None:
                raise ValueError("All pointer-signature args must be named")
            if spec["kind"] == "scalar":
                value = case[name]
                call_args.append(spec["ctype"](value) if not isinstance(value, ctypes._SimpleCData) else value)
                continue
            if name in case and case[name] is not None:
                buf = np.ascontiguousarray(case[name], dtype=spec["numpy_dtype"])
                call_args.append(buf.ctypes.data_as(spec["ctype"]))
                if not spec["const"]:
                    outputs[name] = buf
            else:
                shape = case.get(f"__shape__{name}")
                if shape is None:
                    raise ValueError(f"Output buffer shape for {name!r} not provided")
                buf = np.zeros(shape, dtype=spec["numpy_dtype"])
                call_args.append(buf.ctypes.data_as(spec["ctype"]))
                outputs[name] = buf
        actual_fn(*call_args)
        if len(outputs) == 1:
            return next(iter(outputs.values()))
        return outputs
    try:
        import torch
    except Exception:
        torch = None
    if isinstance(case, np.ndarray) and torch is not None:
        try:
            return fn(torch.from_numpy(case.copy()))
        except Exception:
            return fn(case)
    if isinstance(case, tuple):
        return fn(*case)
    return fn(case)


def _array_summary(value: Any) -> dict[str, Any]:
    try:
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        arr = np.asarray(value)
        arr_float = arr.astype(np.float64, copy=False)
        return {
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "min": float(np.nanmin(arr_float)) if arr.size else None,
            "max": float(np.nanmax(arr_float)) if arr.size else None,
            "nan_count": int(np.isnan(arr_float).sum()) if arr.size else 0,
        }
    except Exception:
        return {"repr": repr(value)}


def _compare_values(a: Any, b: Any, mode: str, rtol: float, atol: float) -> tuple[bool, dict[str, Any]]:
    if hasattr(a, "detach"):
        a = a.detach().cpu().numpy()
    if hasattr(b, "detach"):
        b = b.detach().cpu().numpy()
    arr_a = np.asarray(a)
    arr_b = np.asarray(b)
    if mode == "exact":
        ok = bool(np.array_equal(arr_a, arr_b))
    else:
        ok = bool(np.allclose(arr_a, arr_b, rtol=rtol, atol=atol, equal_nan=True))
    try:
        diff = arr_a.astype(np.float64) - arr_b.astype(np.float64)
        max_abs = float(np.max(np.abs(diff))) if diff.size else 0.0
        denom = np.maximum(np.abs(arr_b.astype(np.float64)), 1e-30)
        max_rel = float(np.max(np.abs(diff) / denom)) if diff.size else 0.0
    except Exception:
        max_abs = math.inf
        max_rel = math.inf
    return ok, {"max_abs_error": max_abs, "max_rel_error": max_rel, "rtol": rtol, "atol": atol}


def _make_pointer_cases(
    input_schema: dict[str, Any],
    parsed_sig: dict[str, Any],
    max_examples: int,
    seed: int = 12345,
) -> list[dict[str, Any]]:
    """Generate dict cases for pointer-signature kernels.

    Schema convention:
      {"params": {"n": {"choices": [8,16,32], "default": 8}, ...},
       "tensors": {"A": {"shape": ["n","n"], "dtype": "float64", "range": [-1,1]},
                   "C": {"shape": ["n","n"], "dtype": "float64", "role": "output"}}}
    """
    rng = np.random.default_rng(seed)
    params_schema = input_schema.get("params", {}) or {}
    tensors_schema_raw = input_schema.get("tensors", {}) or {}
    if isinstance(tensors_schema_raw, list):
        tensors_schema = {entry["name"]: entry for entry in tensors_schema_raw if entry.get("name")}
    else:
        tensors_schema = tensors_schema_raw

    arg_specs = parsed_sig["args"]
    arg_by_name = {spec["name"]: spec for spec in arg_specs if spec.get("name")}

    def _resolve_shape(shape_spec, params_concrete: dict[str, int]) -> tuple[int, ...]:
        resolved = []
        for entry in shape_spec:
            if isinstance(entry, str):
                if entry not in params_concrete:
                    raise ValueError(f"Shape references unknown param: {entry!r}")
                resolved.append(int(params_concrete[entry]))
            else:
                resolved.append(int(entry))
        return tuple(resolved)

    cases: list[dict[str, Any]] = []
    for _ in range(max_examples):
        params_concrete: dict[str, int] = {}
        for name, spec in arg_by_name.items():
            if spec["kind"] != "scalar":
                continue
            schema = params_schema.get(name, {})
            if "choices" in schema:
                params_concrete[name] = int(rng.choice(schema["choices"]))
            elif "default" in schema:
                params_concrete[name] = int(schema["default"])
            else:
                params_concrete[name] = 8

        case: dict[str, Any] = {}
        for name, value in params_concrete.items():
            case[name] = value

        for name, spec in arg_by_name.items():
            if spec["kind"] != "pointer":
                continue
            tensor_schema = tensors_schema.get(name, {})
            shape_spec = tensor_schema.get("shape")
            if shape_spec is None:
                raise ValueError(f"Pointer arg {name!r} missing shape in input_schema.tensors")
            shape = _resolve_shape(shape_spec, params_concrete)
            role = tensor_schema.get("role")
            if role is None:
                role = "input" if spec["const"] else "output"
            if role == "input":
                lo, hi = tensor_schema.get("range", (-1.0, 1.0))
                arr = rng.uniform(float(lo), float(hi), size=shape).astype(spec["numpy_dtype"])
                case[name] = arr
            else:
                case[name] = None
                case[f"__shape__{name}"] = shape

        cases.append(case)
    return cases


def _make_cases(input_schema: dict[str, Any], max_examples: int, arity: int) -> list[Any]:
    kind = input_schema.get("kind", "scalar")
    min_value = float(input_schema.get("min_value", -1000.0))
    max_value = float(input_schema.get("max_value", 1000.0))
    allow_nan = bool(input_schema.get("allow_nan", False))
    allow_inf = bool(input_schema.get("allow_inf", False))
    rng = random.Random(12345)
    cases: list[Any] = []
    if kind in {"auto", "scalar"}:
        edges = [0.0, -0.0, 1.0, -1.0, 1e-30, -1e-30, min_value, max_value, 2.0, -2.0]
        if allow_nan:
            edges.append(float("nan"))
        if allow_inf:
            edges.extend([float("inf"), float("-inf")])
        for value in edges:
            cases.append(tuple([value] * arity) if arity > 1 else value)
        while len(cases) < max_examples:
            values = tuple(rng.uniform(min_value, max_value) for _ in range(arity))
            cases.append(values if arity > 1 else values[0])
        return cases[:max_examples]

    if kind == "tensor":
        shapes = input_schema.get("shapes") or [[1], [4], [2, 3], [16]]
        dtypes = input_schema.get("dtypes") or ["float32"]
        dtype = np.dtype(dtypes[0])
        edge_values = [0.0, 1.0, -1.0]
        for shape in shapes:
            for value in edge_values:
                cases.append(np.full(shape, value, dtype=dtype))
        while len(cases) < max_examples:
            shape = rng.choice(shapes)
            arr = np.asarray(
                [rng.uniform(min_value, max_value) for _ in range(int(np.prod(shape) if shape else 1))],
                dtype=dtype,
            ).reshape(shape)
            cases.append(arr)
        return cases[:max_examples]

    raise ValueError(f"Unsupported input_schema kind for random equivalence: {kind}")


def _call_arity(signature: str | None) -> int:
    if not signature:
        return 1
    match = re.fullmatch(r"\s*\w+\s*\((.*?)\)\s*", signature)
    if not match:
        return 1
    args = [part.strip() for part in match.group(1).split(",") if part.strip()]
    return max(1, len(args))


def _run_random_equivalence_core(config: dict[str, Any]) -> dict[str, Any]:
    source_a = config.get("artifact_a") or config.get("source_a")
    source_b = config.get("artifact_b") or config.get("source_b")
    entrypoints = config.get("entrypoints") or [{"name": "kernel", "signature": "double(double)"}]
    entrypoint = entrypoints[0]
    name = entrypoint.get("name", "kernel")
    signature = entrypoint.get("signature", "double(double)")
    comparison = config.get("comparison") or {}
    mode = comparison.get("mode", "allclose")
    rtol = float(comparison.get("rtol", 1e-5))
    atol = float(comparison.get("atol", 1e-6))
    budget = config.get("budget") or {}
    max_examples = int(budget.get("max_examples", 1000))
    corpus_dir = Path(config.get("corpus_dir") or ".verify/corpus/equivalence").resolve()
    corpus_dir.mkdir(parents=True, exist_ok=True)

    fn_a, kind_a = _load_callable(str(Path(source_a).resolve()), name, signature)
    fn_b, kind_b = _load_callable(str(Path(source_b).resolve()), name, signature)
    if kind_a == "ctypes_pointer" or kind_b == "ctypes_pointer":
        schema = config.get("input_schema") or {}
        parsed_sig = fn_a[1] if kind_a == "ctypes_pointer" else fn_b[1]
        cases = _make_pointer_cases(schema, parsed_sig, max_examples)
        arity = len(parsed_sig["args"])
    else:
        if kind_a == "ctypes_scalar" or kind_b == "ctypes_scalar":
            schema = config.get("input_schema") or {"kind": "scalar"}
        else:
            schema = config.get("input_schema") or {"kind": "tensor", "shapes": [[1]], "dtypes": ["float32"]}
        arity = _call_arity(signature)
        cases = _make_cases(schema, max_examples, arity)

    examples_run = 0
    counterexamples: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        examples_run += 1
        a_out = _call_loaded(fn_a, kind_a, case)
        b_out = _call_loaded(fn_b, kind_b, case)
        ok, diff = _compare_values(a_out, b_out, mode, rtol, atol)
        if ok:
            continue
        path = corpus_dir / f"failing_{index:04d}.pkl"
        with path.open("wb") as handle:
            pickle.dump({"input": case, "a_output": a_out, "b_output": b_out}, handle)
        shape = list(case.shape) if isinstance(case, np.ndarray) else []
        dtype = str(case.dtype) if isinstance(case, np.ndarray) else type(case).__name__
        counterexamples.append(
            {
                "input": {"serialized_path": str(path), "shape": shape, "dtype": dtype, "seed": 12345},
                "a_output_summary": _array_summary(a_out),
                "b_output_summary": _array_summary(b_out),
                "comparison": diff,
            }
        )
        break

    return {
        "verdict": "FAIL" if counterexamples else "PASS",
        "confidence": 0.95 if counterexamples else min(0.9, 0.5 + examples_run / 25000.0),
        "summary": (
            "Randomized equivalence found a mismatch."
            if counterexamples
            else f"{examples_run} randomized equivalence tests passed."
        ),
        "counterexamples": counterexamples,
        "metrics": {
            "examples_run": examples_run,
            "mismatches": len(counterexamples),
            "schema_kind": schema.get("kind", "auto"),
            "rtol": rtol,
            "atol": atol,
            "comparison_mode": mode,
        },
    }


def random_equivalence_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    try:
        result = _run_random_equivalence_core(config)
    except Exception as exc:
        result = {
            "verdict": "ERROR",
            "confidence": 0.0,
            "summary": f"Random equivalence infrastructure error: {exc}",
            "counterexamples": [],
            "metrics": {},
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == "PASS" else 1


async def run_random_equivalence_tests_impl(
    source_a: str,
    source_b: str,
    artifact_a: str | None = None,
    artifact_b: str | None = None,
    task_type: str = "C_TO_C_OPTIMIZATION",
    entrypoints: list[dict[str, Any]] | None = None,
    input_schema: dict[str, Any] | None = None,
    comparison: dict[str, Any] | None = None,
    budget: dict[str, Any] | None = None,
    corpus_dir: str = ".verify/corpus/equivalence",
) -> str:
    del task_type
    root = _resolve_verify_root()
    task_id = _now_task_id("equivalence")
    out_dir = root / "harnesses" / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    config = {
        "source_a": source_a,
        "source_b": source_b,
        "artifact_a": artifact_a,
        "artifact_b": artifact_b,
        "entrypoints": entrypoints or [{"name": "kernel", "signature": "double(double)"}],
        "input_schema": input_schema or {"kind": "scalar"},
        "comparison": comparison or {"mode": "allclose", "rtol": 1e-5, "atol": 1e-6},
        "budget": budget or {"max_examples": 1000, "timeout_s": 300},
        "corpus_dir": corpus_dir,
    }
    config_path = out_dir / "equivalence_config.json"
    script_path = out_dir / "test_equivalence.py"
    _write_json(config_path, config)
    script_path.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(Path.cwd().resolve())!r})\n"
        "from lassi.verification.verification_tools import random_equivalence_main\n"
        "raise SystemExit(random_equivalence_main())\n",
        encoding="utf-8",
    )
    timeout_s = int((budget or {}).get("timeout_s", 300))
    try:
        proc = _run_command([sys.executable, str(script_path), "--config", str(config_path)], timeout_s=timeout_s)
    except subprocess.TimeoutExpired as exc:
        return _json_response(
            "UNSURE",
            0.2,
            "Random equivalence testing timed out.",
            artifacts=[{"kind": "hypothesis_test", "path": str(script_path)}, {"kind": "corpus_dir", "path": corpus_dir}],
            logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
        )
    try:
        result = json.loads(proc.stdout)
    except Exception:
        return _json_response(
            "ERROR",
            0.0,
            "Random equivalence runner did not emit JSON.",
            artifacts=[{"kind": "hypothesis_test", "path": str(script_path)}, {"kind": "config", "path": str(config_path)}],
            logs={"stdout": _short(proc.stdout), "stderr": _short(proc.stderr)},
        )
    return _json_response(
        result.get("verdict", "ERROR"),
        result.get("confidence", 0.0),
        result.get("summary", ""),
        artifacts=[
            {"kind": "hypothesis_test", "path": str(script_path)},
            {"kind": "config", "path": str(config_path)},
            {"kind": "corpus_dir", "path": corpus_dir},
        ],
        counterexamples=result.get("counterexamples", []),
        metrics=result.get("metrics", {}),
        logs={"stdout": _short(proc.stdout), "stderr": _short(proc.stderr)},
    )


def _parse_fuzzer_metrics(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for key, pattern in {
        "execs": r"#(\d+)\s+",
        "coverage": r"cov:\s*(\d+)",
        "features": r"ft:\s*(\d+)",
        "corpus_entries": r"corp:\s*(\d+)",
        "peak_rss_mb": r"rss:\s*(\d+)Mb",
    }.items():
        matches = re.findall(pattern, text)
        if matches:
            metrics[key] = int(matches[-1])
    return metrics


_SCALAR_DTYPE_TO_C: dict[str, str] = {
    "float64": "double",
    "double": "double",
    "float32": "float",
    "float": "float",
    "int64": "int64_t",
    "int32": "int32_t",
    "int16": "int16_t",
    "int8": "int8_t",
    "uint64": "uint64_t",
    "uint32": "uint32_t",
    "uint16": "uint16_t",
    "uint8": "uint8_t",
}


_ROBUSTNESS_WRAPPER_SCALAR_TEMPLATE = r"""
#include <stddef.h>
#include <stdint.h>
#include <string.h>

extern "C" __RET_TYPE__ __ENTRY__(__ARG_TYPE__);

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(__ARG_TYPE__)) return 0;
    __ARG_TYPE__ x;
    memcpy(&x, data, sizeof(__ARG_TYPE__));
    __ENTRY__(x);
    return 0;
}
"""


def _source_has_libfuzzer_entrypoint(source: Path) -> bool:
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "LLVMFuzzerTestOneInput" in text


def _synthesize_robustness_wrapper(
    source: Path,
    entrypoint: str,
    input_schema: dict[str, Any] | None,
    out_dir: Path,
) -> Path | None:
    if not input_schema:
        return None
    kind = str(input_schema.get("kind") or "").lower()
    if kind != "scalar":
        return None
    arg_dtype = str(input_schema.get("dtype") or "float64").lower()
    arg_c = _SCALAR_DTYPE_TO_C.get(arg_dtype)
    if arg_c is None:
        return None
    ret_dtype = str(input_schema.get("return_dtype") or arg_dtype).lower()
    if ret_dtype == "void":
        ret_c: str | None = "void"
    else:
        ret_c = _SCALAR_DTYPE_TO_C.get(ret_dtype)
    if ret_c is None:
        return None
    wrapper = out_dir / "lassi_fuzz_wrapper.cpp"
    wrapper.write_text(
        _ROBUSTNESS_WRAPPER_SCALAR_TEMPLATE
        .replace("__RET_TYPE__", ret_c)
        .replace("__ARG_TYPE__", arg_c)
        .replace("__ENTRY__", entrypoint),
        encoding="utf-8",
    )
    del source  # only needed for caller-side existence checks
    return wrapper


def _compile_fuzzer_if_needed(
    source_path: str,
    artifact: str | None,
    sanitizers: list[str],
    out_dir: Path,
    timeout_s: int,
    entrypoint: str = "kernel",
    input_schema: dict[str, Any] | None = None,
) -> tuple[Path | None, subprocess.CompletedProcess[str] | None]:
    if artifact:
        artifact_path = Path(artifact).resolve()
        return (artifact_path if artifact_path.exists() else None), None
    source = Path(source_path).resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source path not found: {source}")
    compiler = "clang++"
    if shutil.which(compiler) is None:
        raise FileNotFoundError("clang++ not found")
    out = out_dir / "fuzz_target"
    sanitize = _sanitize_flag(["fuzzer", *sanitizers])

    needs_wrapper = not _source_has_libfuzzer_entrypoint(source)
    wrapper_path: Path | None = None
    if needs_wrapper:
        wrapper_path = _synthesize_robustness_wrapper(
            source, entrypoint, input_schema, out_dir
        )
        if wrapper_path is None:
            raise RuntimeError(
                "Source does not define LLVMFuzzerTestOneInput and no synthesizable "
                "input_schema was provided. Pass input_schema={'kind':'scalar',"
                "'dtype':'float64'} (optionally with 'return_dtype') or include "
                "LLVMFuzzerTestOneInput directly in the source."
            )

    cmd = [compiler, "-O1", "-g", "-fno-omit-frame-pointer", sanitize]
    if wrapper_path is not None:
        src_lang = (
            "c++"
            if source.suffix.lower() in {".cc", ".cpp", ".cxx", ".cp", ".c++"}
            else "c"
        )
        cmd.extend(["-x", "c++", str(wrapper_path), "-x", src_lang, str(source)])
    else:
        cmd.append(str(source))
    cmd.extend(["-o", str(out)])

    proc = _run_command(cmd, timeout_s=timeout_s)
    return (out if proc.returncode == 0 else None), proc


async def run_robustness_fuzzer_impl(
    source_path: str,
    artifact: str | None = None,
    entrypoint: str = "kernel",
    input_schema: dict[str, Any] | None = None,
    sanitizers: list[str] | None = None,
    corpus_dir: str = ".verify/corpus/fuzz/source",
    seed_corpus_dir: str | None = None,
    budget: dict[str, Any] | None = None,
    max_len: int = 4096,
) -> str:
    sanitizers = sanitizers or ["address", "undefined"]
    budget = budget or {"max_total_time_s": 300, "jobs": 1, "workers": 1}
    root = _resolve_verify_root()
    task_id = _now_task_id("fuzz")
    out_dir = root / "harnesses" / task_id
    crash_dir = root / "crashes" / task_id
    corpus = Path(corpus_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    crash_dir.mkdir(parents=True, exist_ok=True)
    corpus.mkdir(parents=True, exist_ok=True)

    compile_stdout = ""
    compile_stderr = ""
    try:
        target, compile_proc = _compile_fuzzer_if_needed(
            source_path,
            artifact,
            sanitizers,
            out_dir,
            int(budget.get("max_total_time_s", 300)),
            entrypoint=entrypoint,
            input_schema=input_schema,
        )
    except Exception as exc:
        return _json_response("ERROR", 0.0, f"Fuzzer setup error: {exc}")
    if compile_proc is not None:
        compile_stdout = compile_proc.stdout
        compile_stderr = compile_proc.stderr
        if compile_proc.returncode != 0 or target is None:
            return _json_response(
                "FAIL",
                0.2,
                "Fuzzer target failed to compile.",
                artifacts=[{"kind": "fuzzer_build_dir", "path": str(out_dir)}],
                logs={"stdout": _short(compile_stdout), "stderr": _short(compile_stderr)},
            )
    if target is None:
        return _json_response("ERROR", 0.0, "Fuzzer artifact not found.")

    cmd = [
        str(target),
        str(corpus),
        f"-max_total_time={int(budget.get('max_total_time_s', 300))}",
        f"-jobs={int(budget.get('jobs', 1) or 1)}",
        f"-workers={int(budget.get('workers', 1) or 1)}",
        f"-max_len={int(max_len)}",
        f"-artifact_prefix={str(crash_dir)}/",
    ]
    if budget.get("runs") is not None:
        cmd.append(f"-runs={int(budget['runs'])}")
    if seed_corpus_dir:
        seed = Path(seed_corpus_dir).resolve()
        seed.mkdir(parents=True, exist_ok=True)
        cmd.append(str(seed))
    try:
        proc = _run_command(cmd, cwd=out_dir, timeout_s=int(budget.get("max_total_time_s", 300)) + 30)
    except subprocess.TimeoutExpired as exc:
        return _json_response(
            "UNSURE",
            0.2,
            "Fuzzing timed out before libFuzzer completed.",
            artifacts=[{"kind": "corpus_dir", "path": str(corpus)}, {"kind": "crash_dir", "path": str(crash_dir)}],
            logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
        )
    combined = "\n".join([compile_stdout, compile_stderr, proc.stdout or "", proc.stderr or ""])
    metrics = _parse_fuzzer_metrics(combined)
    metrics["duration_s"] = int(budget.get("max_total_time_s", 300))
    crash_files = [p for p in crash_dir.iterdir() if p.is_file()]
    sanitizer_hit = bool(re.search(r"ERROR: (AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer)", combined))
    failed = proc.returncode != 0 or sanitizer_hit or bool(crash_files)
    counterexamples = [
        {"path": str(p), "kind": "crash", "reproducer_command": f"{target} {p}"}
        for p in crash_files
    ]
    return _json_response(
        "FAIL" if failed else "PASS",
        0.95 if failed else 0.85,
        "Fuzzer found a crash or sanitizer violation." if failed else f"No crashes found in {metrics['duration_s']} seconds.",
        artifacts=[
            {"kind": "fuzzer_target", "path": str(target)},
            {"kind": "corpus_dir", "path": str(corpus)},
            {"kind": "crash_dir", "path": str(crash_dir)},
        ],
        counterexamples=counterexamples,
        metrics=metrics,
        logs={"stdout": _short(proc.stdout), "stderr": _short(proc.stderr)},
    )


_DIFFERENTIAL_DRIVER_SCALAR_DOUBLE = r"""
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <dlfcn.h>

typedef double (*kernel_t)(double);
static kernel_t fa = NULL;
static kernel_t fb = NULL;
static double g_rtol = 1e-9;
static double g_atol = 1e-9;

__attribute__((constructor))
static void _lassi_load(void) {
    const char *pa = getenv("LASSI_LIB_A");
    const char *pb = getenv("LASSI_LIB_B");
    const char *entry = getenv("LASSI_ENTRY");
    const char *rtol_s = getenv("LASSI_RTOL");
    const char *atol_s = getenv("LASSI_ATOL");
    if (!entry || !*entry) entry = "kernel";
    if (rtol_s) g_rtol = strtod(rtol_s, NULL);
    if (atol_s) g_atol = strtod(atol_s, NULL);
    if (!pa || !pb) {
        fprintf(stderr, "LASSI_LIB_A and LASSI_LIB_B must be set\n");
        abort();
    }
    void *ha = dlopen(pa, RTLD_NOW | RTLD_LOCAL);
    if (!ha) { fprintf(stderr, "dlopen A failed: %s\n", dlerror()); abort(); }
    void *hb = dlopen(pb, RTLD_NOW | RTLD_LOCAL);
    if (!hb) { fprintf(stderr, "dlopen B failed: %s\n", dlerror()); abort(); }
    fa = (kernel_t) dlsym(ha, entry);
    fb = (kernel_t) dlsym(hb, entry);
    if (!fa || !fb) {
        fprintf(stderr, "dlsym %s failed\n", entry);
        abort();
    }
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < sizeof(double)) return 0;
    double x;
    memcpy(&x, data, sizeof(double));
    if (!isfinite(x)) return 0;
    double a = fa(x);
    double b = fb(x);
    int a_fin = isfinite(a);
    int b_fin = isfinite(b);
    if (!a_fin && !b_fin) return 0;
    if (a_fin != b_fin) {
        fprintf(stderr, "DIFFERENTIAL MISMATCH (finiteness) at x=%a a=%a b=%a\n", x, a, b);
        abort();
    }
    double diff = fabs(a - b);
    double tol = g_atol + g_rtol * fabs(b);
    if (diff > tol) {
        fprintf(stderr, "DIFFERENTIAL MISMATCH at x=%a a=%a b=%a diff=%a tol=%a\n",
                x, a, b, diff, tol);
        abort();
    }
    return 0;
}
"""


def _signature_supports_diff_fuzz(signature: str | None) -> bool:
    if not signature:
        return True
    try:
        ret, args = _parse_ctypes_signature(signature)
    except ValueError:
        return False
    return ret is ctypes.c_double and args == [ctypes.c_double]


def _build_diff_fuzz_artifacts(
    source_a: Path,
    source_b: Path,
    entrypoint: str,
    sanitizers: list[str],
    rtol: float,
    atol: float,
    work_dir: Path,
    timeout_s: int,
) -> tuple[Path, Path, Path, list[str]]:
    work_dir.mkdir(parents=True, exist_ok=True)
    cxx = shutil.which("clang++")
    cc = shutil.which("clang")
    if cxx is None or cc is None:
        raise FileNotFoundError("clang and clang++ are required for differential fuzzer synthesis")

    lib_a = work_dir / f"{source_a.stem}_a.so"
    lib_b = work_dir / f"{source_b.stem}_b.so"
    driver_src = work_dir / "differential_driver.cc"
    driver_bin = work_dir / "differential_fuzz"
    log_lines: list[str] = []

    def _run(cmd: list[str]) -> None:
        proc = _run_command(cmd, timeout_s=timeout_s)
        log_lines.append("$ " + " ".join(cmd))
        log_lines.append(proc.stdout or "")
        log_lines.append(proc.stderr or "")
        if proc.returncode != 0:
            raise RuntimeError(f"Build step failed:\n{proc.stderr or proc.stdout}")

    _run([cc, "-O2", "-fPIC", "-shared", str(source_a), "-o", str(lib_a)])
    _run([cc, "-O2", "-fPIC", "-shared", str(source_b), "-o", str(lib_b)])

    driver_src.write_text(_DIFFERENTIAL_DRIVER_SCALAR_DOUBLE, encoding="utf-8")
    sanitize_flag = _sanitize_flag(["fuzzer", *sanitizers])
    _run([
        cxx,
        "-O1",
        "-g",
        "-fno-omit-frame-pointer",
        sanitize_flag,
        str(driver_src),
        "-ldl",
        "-o",
        str(driver_bin),
    ])
    return driver_bin, lib_a, lib_b, log_lines


async def run_differential_fuzzer_impl(
    source_a: str,
    source_b: str,
    artifact: str | None = None,
    task_type: str = "C_TO_C_OPTIMIZATION",
    comparison: dict[str, Any] | None = None,
    corpus_dir: str = ".verify/corpus/fuzz/differential",
    seed_corpus_dir: str | None = None,
    budget: dict[str, Any] | None = None,
    max_len: int = 4096,
) -> str:
    del task_type
    if artifact:
        return await run_robustness_fuzzer_impl(
            source_path=artifact,
            artifact=artifact,
            corpus_dir=corpus_dir,
            seed_corpus_dir=seed_corpus_dir,
            budget=budget,
            max_len=max_len,
        )

    comparison = comparison or {}
    rtol = float(comparison.get("rtol", 1e-9))
    atol = float(comparison.get("atol", 1e-9))
    entrypoint = comparison.get("entrypoint", "kernel")
    signature = comparison.get("signature", "double(double)")
    if not _signature_supports_diff_fuzz(signature):
        return _json_response(
            "UNSURE",
            0.25,
            f"Differential fuzz driver synthesis currently supports only double(double) kernels; got: {signature}",
            metrics={"requires_artifact": True},
        )

    sanitizers = list(comparison.get("sanitizers") or ["address", "undefined"])
    budget = budget or {"max_total_time_s": 30, "jobs": 1, "workers": 1}
    root = _resolve_verify_root()
    task_id = _now_task_id("difffuzz")
    work_dir = root / "harnesses" / task_id
    corpus = Path(corpus_dir).resolve()
    crash_dir = root / "crashes" / task_id
    corpus.mkdir(parents=True, exist_ok=True)
    crash_dir.mkdir(parents=True, exist_ok=True)

    source_a_path = Path(source_a).resolve()
    source_b_path = Path(source_b).resolve()
    if not source_a_path.exists() or not source_b_path.exists():
        return _json_response("ERROR", 0.0, "source_a or source_b not found")

    try:
        driver_bin, lib_a, lib_b, build_log = _build_diff_fuzz_artifacts(
            source_a_path,
            source_b_path,
            entrypoint,
            sanitizers,
            rtol,
            atol,
            work_dir,
            timeout_s=int(budget.get("max_total_time_s", 30)) + 30,
        )
    except Exception as exc:
        return _json_response(
            "FAIL",
            0.2,
            f"Differential fuzz driver build failed: {exc}",
            artifacts=[{"kind": "harness_dir", "path": str(work_dir)}],
        )

    cmd = [
        str(driver_bin),
        str(corpus),
        f"-max_total_time={int(budget.get('max_total_time_s', 30))}",
        f"-jobs={int(budget.get('jobs', 1) or 1)}",
        f"-workers={int(budget.get('workers', 1) or 1)}",
        f"-max_len={int(max_len)}",
        f"-artifact_prefix={str(crash_dir)}/",
    ]
    if budget.get("runs") is not None:
        cmd.append(f"-runs={int(budget['runs'])}")
    if seed_corpus_dir:
        seed = Path(seed_corpus_dir).resolve()
        seed.mkdir(parents=True, exist_ok=True)
        cmd.append(str(seed))

    env = os.environ.copy()
    env.update({
        "LASSI_LIB_A": str(lib_a),
        "LASSI_LIB_B": str(lib_b),
        "LASSI_ENTRY": entrypoint,
        "LASSI_RTOL": repr(rtol),
        "LASSI_ATOL": repr(atol),
    })

    try:
        proc = _run_command(cmd, cwd=work_dir, timeout_s=int(budget.get("max_total_time_s", 30)) + 30, env=env)
    except subprocess.TimeoutExpired as exc:
        return _json_response(
            "UNSURE",
            0.2,
            "Differential fuzzing timed out.",
            artifacts=[
                {"kind": "fuzzer_target", "path": str(driver_bin)},
                {"kind": "corpus_dir", "path": str(corpus)},
                {"kind": "crash_dir", "path": str(crash_dir)},
            ],
            logs={"stdout": _short(exc.stdout), "stderr": _short(exc.stderr)},
        )

    combined = "\n".join(["\n".join(build_log), proc.stdout or "", proc.stderr or ""])
    metrics = _parse_fuzzer_metrics(combined)
    metrics["duration_s"] = int(budget.get("max_total_time_s", 30))
    crash_files = [p for p in crash_dir.iterdir() if p.is_file()]
    differential_hit = "DIFFERENTIAL MISMATCH" in combined
    sanitizer_hit = bool(re.search(r"ERROR: (AddressSanitizer|UndefinedBehaviorSanitizer|LeakSanitizer)", combined))
    failed = proc.returncode != 0 or sanitizer_hit or differential_hit or bool(crash_files)
    counterexamples = [
        {"path": str(p), "kind": "differential_mismatch" if differential_hit else "crash",
         "reproducer_command": f"LASSI_LIB_A={lib_a} LASSI_LIB_B={lib_b} {driver_bin} {p}"}
        for p in crash_files
    ]
    summary = (
        "Differential fuzzer found a mismatch or crash."
        if failed
        else f"No differential mismatches found in {metrics['duration_s']} seconds."
    )
    return _json_response(
        "FAIL" if failed else "PASS",
        0.95 if failed else 0.8,
        summary,
        artifacts=[
            {"kind": "fuzzer_target", "path": str(driver_bin)},
            {"kind": "shared_library", "path": str(lib_a)},
            {"kind": "shared_library", "path": str(lib_b)},
            {"kind": "corpus_dir", "path": str(corpus)},
            {"kind": "crash_dir", "path": str(crash_dir)},
        ],
        counterexamples=counterexamples,
        metrics=metrics,
        logs={"stdout": _short(proc.stdout), "stderr": _short(proc.stderr)},
    )


async def synthesize_verification_report_impl(
    task_id: str | None = None,
    task_type: str = "C_TO_C_OPTIMIZATION",
    tool_results: list[dict[str, Any]] | dict[str, Any] | None = None,
    output_dir: str = ".verify/reports",
) -> str:
    task_id = task_id or _now_task_id("verify")
    results: list[dict[str, Any]]
    if tool_results is None:
        results = []
    elif isinstance(tool_results, dict):
        results = list(tool_results.values()) if all(isinstance(v, dict) for v in tool_results.values()) else [tool_results]
    else:
        results = tool_results

    statuses = [r.get("verdict", "ERROR") for r in results]
    if "FAIL" in statuses:
        status = "FAIL"
    elif "ERROR" in statuses or "UNSURE" in statuses or not statuses:
        status = "UNSURE"
    else:
        status = "PASS"
    confidence = min([float(r.get("confidence", 0.0)) for r in results], default=0.0)
    counterexamples: list[dict[str, Any]] = []
    artifacts: list[Any] = []
    for result in results:
        counterexamples.extend(result.get("counterexamples", []) or [])
        artifacts.extend(result.get("artifacts", []) or [])

    report = {
        "task_id": task_id,
        "task_type": task_type,
        "status": status,
        "confidence": confidence,
        "summary": f"Aggregated {len(results)} verification tool result(s); final status is {status}.",
        "tool_statuses": statuses,
        "counterexamples": counterexamples,
        "artifacts": artifacts,
    }
    out = Path(output_dir).resolve()
    json_path = _write_json(out / f"{task_id}.json", report)
    md_path = out / f"{task_id}.md"
    md_path.write_text(
        "\n".join(
            [
                f"# Verification Report: {task_id}",
                "",
                f"- task_type: {task_type}",
                f"- status: {status}",
                f"- confidence: {confidence}",
                f"- tool_results: {len(results)}",
                f"- counterexamples: {len(counterexamples)}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return _json_response(
        status if status in {"PASS", "FAIL"} else "UNSURE",
        confidence,
        report["summary"],
        artifacts=[{"kind": "report_json", "path": str(json_path)}, {"kind": "report_markdown", "path": str(md_path)}],
        counterexamples=counterexamples,
        metrics={"tool_results": len(results), "tool_statuses": statuses},
    )
