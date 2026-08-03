from __future__ import annotations

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np

from .types import Diagnostic

if TYPE_CHECKING:
    from .config import RunConfig


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
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout_s)
    except TimeoutError:
        process.kill()
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
    code, build_out, build_err = await _run(
        build, cwd=config.project.root, timeout_s=config.oracle.timeout_s
    )
    if code:
        raise RuntimeError(f"oracle build failed ({code}): {build_err[-4000:]}")
    run = _format_command(config.oracle.run, values)
    code, run_out, run_err = await _run(
        run, cwd=config.project.root, timeout_s=config.oracle.timeout_s
    )
    if code:
        raise RuntimeError(f"oracle execution failed ({code}): {run_err[-4000:]}")
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
    return OracleResult(output, result, build_out + build_err, run_out + run_err)


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


def _runner_environment() -> dict[str, str]:
    env = os.environ.copy()
    package_root = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")
    return env


async def execute_candidate(
    config: RunConfig,
    module_path: Path,
    *,
    precision: str,
    device: str,
    artifact_path: Path,
) -> tuple[np.ndarray | None, str, Diagnostic | None]:
    command = [
        sys.executable,
        "-m",
        "lassi_x.runner",
        "--module",
        str(module_path),
        "--device",
        device,
        "--precision",
        precision,
        "--output",
        str(artifact_path),
    ]
    if config.oracle.input_fixture:
        command += [
            "--fixture",
            str(config.resolve_project_path(config.oracle.input_fixture)),
        ]
    try:
        code, stdout, stderr = await _run(
            command,
            cwd=config.project.root,
            timeout_s=config.arena.timeout_s,
            env=_runner_environment(),
        )
    except TimeoutError:
        return None, "", Diagnostic(gate="runtime", message="candidate execution timed out")
    try:
        payload = json.loads(stdout.strip().splitlines()[-1]) if stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    if code or not payload.get("ok") or not artifact_path.exists():
        return (
            None,
            "",
            Diagnostic(
                gate="runtime",
                message=str(payload.get("error") or "candidate execution failed"),
                command=command,
                exit_code=code,
                stderr=(stderr or stdout)[-4000:],
            ),
        )
    return np.load(artifact_path), str(payload.get("output_dtype") or ""), None


async def validate_candidate(
    config: RunConfig,
    module_path: Path,
    oracle: OracleResult,
    artifact_dir: Path,
) -> ValidationResult:
    if not module_path.is_file():
        return ValidationResult(
            False,
            Diagnostic(gate="write", message=f"candidate did not create {module_path}"),
            None,
        )
    command = [sys.executable, "-m", "py_compile", str(module_path)]
    code, stdout, stderr = await _run(
        command, cwd=config.project.root, timeout_s=config.arena.timeout_s
    )
    if code:
        return ValidationResult(
            False,
            Diagnostic(
                gate="compile",
                message="candidate failed Python byte-compilation",
                command=command,
                exit_code=code,
                stderr=(stderr or stdout)[-4000:],
            ),
            None,
        )
    output_path = artifact_dir / "fp64.npy"
    output, output_dtype, diagnostic = await execute_candidate(
        config,
        module_path,
        precision="fp64",
        device="cpu",
        artifact_path=output_path,
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
    base_module: Path,
    compensated_module: Path,
    artifact_dir: Path,
) -> ValidationResult:
    base, _, diagnostic = await execute_candidate(
        config,
        base_module,
        precision="fp32",
        device="cpu",
        artifact_path=artifact_dir / "base-fp32.npy",
    )
    if diagnostic or base is None:
        return ValidationResult(False, diagnostic, None)
    compensated, dtype, diagnostic = await execute_candidate(
        config,
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
