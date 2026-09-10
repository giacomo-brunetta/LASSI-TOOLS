from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np

from .protocol import ExecRequest
from .types import Diagnostic

if TYPE_CHECKING:
    from .config import RunConfig
    from .execution import ExecutionBackend


def _format_command(command: list[str], values: dict[str, str]) -> list[str]:
    return [part.format_map(values) for part in command]


async def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout_s: float,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_s)
    except TimeoutError:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()
        raise
    return (
        int(process.returncode or 0),
        stdout.decode(errors="replace"),
        stderr.decode(errors="replace"),
    )


def load_reference_output(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return cast("np.ndarray", np.load(path).astype(np.float64).reshape(-1))
    try:
        value = np.loadtxt(path, delimiter=",", dtype=np.float64)
    except ValueError:
        value = np.loadtxt(path, dtype=np.float64)
    return np.asarray(value, dtype=np.float64).reshape(-1)


def scrape_polybench_dump(text: str) -> np.ndarray:
    start = text.find("==BEGIN DUMP_ARRAYS==")
    end = text.find("==END", start + 1)
    block = text[start:end] if start >= 0 and end > start else text
    values: list[float] = []
    for line in block.splitlines():
        stripped = line.strip()
        if (
            not stripped
            or stripped.startswith("==")
            or stripped.startswith("begin dump:")
            or stripped.startswith("end")
        ):
            continue
        for token in stripped.split():
            try:
                values.append(float(token))
            except ValueError:
                continue
    if not values:
        raise ValueError("PolyBench output contains no numeric dump values")
    return np.asarray(values, dtype=np.float64)


@dataclass(slots=True)
class OracleResult:
    output_path: Path
    values: np.ndarray
    build_stdout: str = ""
    run_stdout: str = ""
    source_sha256: str = ""
    output_sha256: str = ""
    determinism_runs: int = 1


async def build_oracle(config: RunConfig, run_dir: Path) -> OracleResult:
    oracle_dir = run_dir / "oracle"
    oracle_dir.mkdir(parents=True, exist_ok=True)
    output = oracle_dir / config.oracle.output.name
    fixture = (
        config.resolve_project_path(config.oracle.input_fixture)
        if config.oracle.input_fixture
        else Path("")
    )
    values = {
        "reference": str(config.resolve_project_path(config.kernel.reference)),
        "output": str(output),
        "input": str(fixture),
        "project": str(config.project.root),
        "oracle_dir": str(oracle_dir),
    }
    build = _format_command(config.oracle.build, values)
    (oracle_dir / "build-command.json").write_text(json.dumps(build, indent=2) + "\n")
    try:
        code, build_out, build_err = await _run(
            build, cwd=config.project.root, timeout_s=config.oracle.timeout_s
        )
    except TimeoutError as exc:
        raise RuntimeError(
            f"oracle build timed out after {config.oracle.timeout_s:g} seconds; "
            f"command saved in {oracle_dir}"
        ) from exc
    (oracle_dir / "build.stdout").write_text(build_out)
    (oracle_dir / "build.stderr").write_text(build_err)
    if code:
        raise RuntimeError(
            f"oracle build failed ({code}); complete stdout/stderr saved in {oracle_dir}: "
            f"{build_err[-4000:]}"
        )
    run = _format_command(config.oracle.run, values)
    (oracle_dir / "run-command.json").write_text(json.dumps(run, indent=2) + "\n")
    outputs: list[np.ndarray] = []
    combined_run_output: list[str] = []
    for attempt in range(config.oracle.determinism_runs):
        try:
            code, run_out, run_err = await _run(
                run, cwd=config.project.root, timeout_s=config.oracle.timeout_s
            )
        except TimeoutError as exc:
            raise RuntimeError(
                f"oracle execution timed out after {config.oracle.timeout_s:g} seconds; "
                f"command saved in {oracle_dir}"
            ) from exc
        suffix = "" if attempt == 0 else f"-{attempt + 1}"
        (oracle_dir / f"run{suffix}.stdout").write_text(run_out)
        (oracle_dir / f"run{suffix}.stderr").write_text(run_err)
        if code:
            raise RuntimeError(
                f"oracle execution failed ({code}); complete stdout/stderr saved in "
                f"{oracle_dir}: {run_err[-4000:]}"
            )
        captured = None
        if config.oracle.capture == "stdout":
            captured = run_out
        elif config.oracle.capture == "stderr":
            captured = run_err
        if captured is not None:
            if config.oracle.format == "polybench":
                parsed = scrape_polybench_dump(captured)
                output.write_text("".join(f"{value:.17g}\n" for value in parsed))
            else:
                output.write_text(captured)
        if not output.is_file():
            raise RuntimeError(f"oracle did not produce configured output: {output}")
        result = load_reference_output(output)
        if not np.isfinite(result).all():
            raise RuntimeError("C/C++ FP64 oracle contains NaN or Inf")
        outputs.append(result.copy())
        combined_run_output.append(run_out + run_err)
    if any(not np.array_equal(outputs[0], repeated, equal_nan=True) for repeated in outputs[1:]):
        raise RuntimeError(
            f"C/C++ FP64 oracle was nondeterministic across "
            f"{config.oracle.determinism_runs} executions"
        )
    reference_path = config.resolve_project_path(config.kernel.reference)
    return OracleResult(
        output,
        outputs[0],
        build_out + build_err,
        "".join(combined_run_output),
        hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        hashlib.sha256(output.read_bytes()).hexdigest(),
        config.oracle.determinism_runs,
    )


def compare_outputs(
    candidate: np.ndarray,
    reference: np.ndarray,
    *,
    rtol: float,
    atol: float,
    max_mismatches: int,
) -> tuple[bool, Diagnostic | None, dict[str, float]]:
    candidate = np.asarray(candidate, dtype=np.float64).reshape(-1)
    reference = np.asarray(reference, dtype=np.float64).reshape(-1)
    if candidate.shape != reference.shape:
        return (
            False,
            Diagnostic(
                gate="shape",
                message="candidate output shape differs from C/C++ FP64 oracle",
                expected_shape=list(reference.shape),
                actual_shape=list(candidate.shape),
            ),
            {},
        )
    if not np.isfinite(candidate).all():
        return False, Diagnostic(gate="finite", message="candidate contains NaN or Inf"), {}
    delta = np.abs(candidate - reference)
    denominator = np.maximum(np.abs(reference), max(atol, 1e-30))
    relative = delta / denominator
    reference_norm = max(float(np.linalg.norm(reference)), 1e-30)
    metrics = {
        "max_abs_error": float(delta.max(initial=0.0)),
        "max_rel_error": float(relative.max(initial=0.0)),
        "relative_l2": float(np.linalg.norm(candidate - reference) / reference_norm),
    }
    close = np.isclose(candidate, reference, rtol=rtol, atol=atol)
    if bool(close.all()):
        return True, None, metrics
    mismatches = []
    for index in np.flatnonzero(~close)[:max_mismatches]:
        mismatches.append(
            {
                "index": int(index),
                "reference": float(reference[index]),
                "candidate": float(candidate[index]),
                "abs_error": float(delta[index]),
                "rel_error": float(relative[index]),
            }
        )
    return (
        False,
        Diagnostic(
            gate="equivalence",
            message="candidate does not match the original C/C++ FP64 oracle",
            max_abs_error=metrics["max_abs_error"],
            max_rel_error=metrics["max_rel_error"],
            relative_l2=metrics["relative_l2"],
            mismatches=mismatches,
        ),
        metrics,
    )


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    diagnostic: Diagnostic | None
    output: np.ndarray | None
    output_dtype: str = ""
    metrics: dict[str, float] | None = None


def fixture_relative_path(config: RunConfig) -> str | None:
    """Return the staged workspace-relative path of the oracle input fixture.

    Args:
        config: Validated run configuration.

    Returns:
        The path beneath ``reference/`` the fixture is staged at, or ``None``
        when the run has no fixture.

    """
    if not config.oracle.input_fixture:
        return None
    return f"reference/{config.resolve_project_path(config.oracle.input_fixture).name}"


async def _module_exists(backend: ExecutionBackend, workspace: str, module_name: str) -> bool:
    """Check whether the agent produced its target module in the workspace.

    Args:
        backend: Backend serving the workspace.
        workspace: Workspace identifier.
        module_name: Workspace-relative module path.

    Returns:
        Whether the file exists.

    """
    from .protocol import ListDir  # noqa: PLC0415

    try:
        listing = await backend.list_dir(ListDir(workspace=workspace, path="."))
    except Exception:  # noqa: BLE001  # remote errors mean "not observable"
        return False
    return any(entry.name == module_name and entry.kind == "file" for entry in listing.entries)


async def execute_candidate(
    config: RunConfig,
    backend: ExecutionBackend,
    workspace: str,
    module_name: str,
    *,
    precision: str,
    device: str,
    artifact_path: Path,
) -> tuple[np.ndarray | None, str, Diagnostic | None]:
    """Run one candidate module through the runner on its execution backend.

    The runner executes inside the workspace on the backend's resource and its
    ``.npy`` output is fetched back into the local artifact directory, so the
    numeric comparison itself always happens on the harness.

    Args:
        config: Validated run configuration.
        backend: Backend serving the workspace.
        workspace: Workspace identifier holding the module.
        module_name: Workspace-relative module path.
        precision: Requested computation precision.
        device: Torch device string on the executing resource.
        artifact_path: Local file that receives the fetched output array.

    Returns:
        The flattened FP64 output, the reported output dtype, and a diagnostic
        when execution failed.

    """
    from .execution import fetch_bytes  # noqa: PLC0415

    handshake = await backend.cached_handshake()
    remote_output = f".lassi/{artifact_path.name}"
    command = [
        handshake.python_executable,
        "-m",
        "lassi_x.runner",
        "--module",
        module_name,
        "--device",
        device,
        "--precision",
        precision,
        "--output",
        remote_output,
    ]
    fixture = fixture_relative_path(config)
    if fixture is not None:
        command += ["--fixture", fixture]
    command += ["--dataset", config.kernel.validation_dataset]
    result = await backend.execute(
        ExecRequest(workspace=workspace, argv=command, timeout_s=config.arena.timeout_s)
    )
    if result.timed_out:
        return None, "", Diagnostic(gate="runtime", message="candidate execution timed out")
    stdout = result.stdout.strip()
    try:
        payload = json.loads(stdout.splitlines()[-1]) if stdout else {}
    except json.JSONDecodeError:
        payload = {}
    if result.exit_code != 0 or not payload.get("ok"):
        return (
            None,
            "",
            Diagnostic(
                gate="runtime",
                message=str(payload.get("error") or "candidate execution failed"),
                command=command,
                exit_code=result.exit_code,
                stderr=(result.stderr or result.stdout)[-4000:],
            ),
        )
    try:
        data = await fetch_bytes(backend, workspace, remote_output)
    except Exception as exc:  # noqa: BLE001  # remote fetch failures become diagnostics
        return (
            None,
            "",
            Diagnostic(
                gate="runtime",
                message=f"candidate output could not be retrieved: {exc}",
                command=command,
            ),
        )
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_bytes(data)
    return np.load(artifact_path), str(payload.get("output_dtype") or ""), None


async def validate_candidate(
    config: RunConfig,
    backend: ExecutionBackend,
    workspace: str,
    oracle: OracleResult,
    artifact_dir: Path,
    *,
    module_name: str = "candidate.py",
) -> ValidationResult:
    """Validate one candidate module against the authoritative C/C++ oracle.

    Args:
        config: Validated run configuration and equivalence tolerances.
        backend: Backend serving the candidate workspace.
        workspace: Workspace identifier holding the module.
        oracle: Authoritative output produced from the original C/C++ reference.
        artifact_dir: Local directory receiving execution artifacts.
        module_name: Workspace-relative module path.

    Returns:
        The validation outcome with diagnostics and numeric metrics.

    """
    handshake = await backend.cached_handshake()
    if not await _module_exists(backend, workspace, module_name):
        return ValidationResult(
            False,
            Diagnostic(
                gate="write",
                message=f"candidate did not create {module_name} in workspace {workspace}",
            ),
            None,
        )
    command = [handshake.python_executable, "-m", "py_compile", module_name]
    compile_result = await backend.execute(
        ExecRequest(workspace=workspace, argv=command, timeout_s=config.arena.timeout_s)
    )
    if not compile_result.ok:
        return ValidationResult(
            False,
            Diagnostic(
                gate="compile",
                message=(
                    "candidate Python byte-compilation timed out"
                    if compile_result.timed_out
                    else "candidate failed Python byte-compilation"
                ),
                command=command,
                exit_code=compile_result.exit_code,
                stderr=(compile_result.stderr or compile_result.stdout)[-4000:],
            ),
            None,
        )
    output, output_dtype, diagnostic = await execute_candidate(
        config,
        backend,
        workspace,
        module_name,
        precision="fp64",
        device="cpu",
        artifact_path=artifact_dir / "fp64.npy",
    )
    if diagnostic or output is None:
        return ValidationResult(False, diagnostic, None)
    ok, diagnostic, metrics = compare_outputs(
        output,
        oracle.values,
        rtol=config.arena.equivalence.rtol,
        atol=config.arena.equivalence.atol,
        max_mismatches=config.arena.equivalence.max_mismatches,
    )
    return ValidationResult(ok, diagnostic, output, output_dtype, metrics)


async def validate_fp32_collapse(
    config: RunConfig,
    backend: ExecutionBackend,
    base_workspace: str,
    compensated_workspace: str,
    artifact_dir: Path,
    *,
    base_module: str = "candidate.py",
    compensated_module: str = "candidate.py",
) -> ValidationResult:
    """Require compensation to reproduce the base algorithm at FP32.

    Args:
        config: Validated run configuration and equivalence tolerances.
        backend: Backend serving both workspaces.
        base_workspace: Workspace of the validated base candidate.
        compensated_workspace: Workspace of the compensated variant.
        artifact_dir: Local directory receiving execution artifacts.
        base_module: Workspace-relative base module path.
        compensated_module: Workspace-relative compensated module path.

    Returns:
        The validation outcome with diagnostics and numeric metrics.

    """
    base, _, diagnostic = await execute_candidate(
        config,
        backend,
        base_workspace,
        base_module,
        precision="fp32",
        device="cpu",
        artifact_path=artifact_dir / "base-fp32.npy",
    )
    if diagnostic or base is None:
        return ValidationResult(False, diagnostic, None)
    compensated, dtype, diagnostic = await execute_candidate(
        config,
        backend,
        compensated_workspace,
        compensated_module,
        precision="fp32",
        device="cpu",
        artifact_path=artifact_dir / "compensated-fp32.npy",
    )
    if diagnostic or compensated is None:
        return ValidationResult(False, diagnostic, None)
    ok, diagnostic, metrics = compare_outputs(
        compensated,
        base,
        rtol=config.arena.equivalence.rtol,
        atol=config.arena.equivalence.atol,
        max_mismatches=config.arena.equivalence.max_mismatches,
    )
    if diagnostic:
        diagnostic.message = "compensation does not collapse to the base algorithm at FP32"
    return ValidationResult(ok, diagnostic, compensated, dtype, metrics)
