from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import os
import signal
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

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
    input_contract_path: Path | None = None


async def build_oracle(config: RunConfig, run_dir: Path) -> OracleResult:
    if config.oracle.fixture_spec is not None:
        from .c_fixtures import build_fixture_oracle  # noqa: PLC0415

        return await build_fixture_oracle(config, run_dir)
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
    input_contract_path = None
    if config.arena.input_check.enabled:
        from .c_inputs import build_input_contract  # noqa: PLC0415

        supplied = config.arena.input_check.contracts.get(config.kernel.validation_dataset)
        if supplied is not None:
            from .input_contract import load_contract  # noqa: PLC0415

            input_contract_path = config.resolve_project_path(supplied)
            _, metadata = load_contract(input_contract_path)
            if metadata.get("dataset") != config.kernel.validation_dataset:
                raise ValueError("configured input contract has the wrong dataset")
        else:
            input_contract_path = await build_input_contract(config, oracle_dir / "input-contract")
    return OracleResult(
        output,
        outputs[0],
        build_out + build_err,
        "".join(combined_run_output),
        hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        hashlib.sha256(output.read_bytes()).hexdigest(),
        config.oracle.determinism_runs,
        input_contract_path,
    )


def compare_outputs(
    candidate: np.ndarray,
    reference: np.ndarray,
    *,
    rtol: float,
    atol: float,
    max_mismatches: int,
    component_sizes: list[int] | None = None,
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
    aggregate_relative_l2 = float(np.linalg.norm(candidate - reference) / reference_norm)
    component_relative_l2 = [aggregate_relative_l2]
    if component_sizes and sum(component_sizes) == candidate.size:
        component_relative_l2 = []
        offset = 0
        for size in component_sizes:
            candidate_component = candidate[offset : offset + size]
            reference_component = reference[offset : offset + size]
            component_norm = max(float(np.linalg.norm(reference_component)), 1e-30)
            component_relative_l2.append(
                float(np.linalg.norm(candidate_component - reference_component) / component_norm)
            )
            offset += size
    metrics = {
        "max_abs_error": float(delta.max(initial=0.0)),
        "max_rel_error": float(relative.max(initial=0.0)),
        # The worst top-level output prevents a large tensor from hiding the
        # failure of a smaller returned output. Single-output candidates reduce
        # to the conventional aggregate relative L2 metric.
        "relative_l2": max(component_relative_l2, default=aggregate_relative_l2),
        "aggregate_relative_l2": aggregate_relative_l2,
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
    input_contract: Path | None = None,
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
    from .execution import fetch_bytes, put_bytes  # noqa: PLC0415

    handshake = await backend.cached_handshake()
    remote_output = f".lassi/{artifact_path.name}"
    command = [
        handshake.python_executable,
        "-m",
        "lassi_x.candidate_runner",
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
    remote_input_report = f".lassi/{artifact_path.stem}-inputs.json"
    remote_input_snapshot = f".lassi/inputs-{uuid.uuid4().hex}.npz"
    if input_contract is not None:
        remote_contract = ".lassi/trusted-input-contract.npz"
        await put_bytes(backend, workspace, remote_contract, input_contract.read_bytes())
        # Execute the harness runner even on endpoints with older packages.
        for name, remote in (
            ("input_contract.py", ".lassi-input-contract.py"),
            ("candidate_runner.py", ".lassi-runner.py"),
        ):
            await put_bytes(backend, workspace, remote, (Path(__file__).parent / name).read_bytes())
        bootstrap = (
            "import importlib.util,sys,lassi_x; "
            "s=importlib.util.spec_from_file_location("
            "'lassi_x.input_contract','.lassi-input-contract.py'); "
            "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m); "
            "import lassi_x.candidate_runner as r; "
            "exec(compile(open('.lassi-runner.py').read(),'.lassi-runner.py','exec'),r.__dict__); "
            "sys.argv=['lassi_x.candidate_runner',*sys.argv[1:]];sys.exit(r.main())"
        )
        command[1:3] = ["-c", bootstrap]
        check = config.arena.input_check
        command += [
            "--input-contract",
            remote_contract,
            "--input-report",
            remote_input_report,
            "--input-snapshot",
            remote_input_snapshot,
            "--input-bindings",
            json.dumps(check.bindings),
            "--input-rtol",
            str(check.rtol),
            "--input-atol",
            str(check.atol),
        ]
    result = await backend.execute(
        ExecRequest(workspace=workspace, argv=command, timeout_s=config.arena.timeout_s)
    )
    if result.timed_out:
        return (
            None,
            "",
            Diagnostic(
                gate="runtime",
                message=f"candidate execution timed out after {config.arena.timeout_s:g} seconds",
            ),
        )
    stdout = result.stdout.strip()
    try:
        payload = json.loads(stdout.splitlines()[-1]) if stdout else {}
    except json.JSONDecodeError:
        payload = {}
    if input_contract is not None:
        from .input_contract import compare_input_arrays, load_contract  # noqa: PLC0415

        try:
            snapshot_data = await fetch_bytes(backend, workspace, remote_input_snapshot)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path = artifact_path.with_suffix(".inputs.npz")
            snapshot_path.write_bytes(snapshot_data)
            with np.load(snapshot_path, allow_pickle=False) as archive:
                actual_inputs = {name: archive[name] for name in archive.files}
            expected_inputs, metadata = load_contract(input_contract)
            check = config.arena.input_check
            report = compare_input_arrays(
                actual_inputs,
                expected_inputs,
                metadata,
                bindings=check.bindings,
                rtol=check.rtol,
                atol=check.atol,
                precision=precision,
            )
            artifact_path.with_suffix(".inputs.json").write_text(
                json.dumps(report, indent=2) + "\n"
            )
            if not report["ok"]:
                return None, "", Diagnostic(gate="inputs", message=json.dumps(report["errors"]))
        except Exception as exc:  # noqa: BLE001
            return (
                None,
                "",
                Diagnostic(gate="inputs", message=f"input snapshot unavailable or invalid: {exc}"),
            )
    if result.exit_code != 0 or not payload.get("ok"):
        return (
            None,
            "",
            Diagnostic(
                gate=str(payload.get("gate") or "runtime"),
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
    """Require numerical validation and, when configured, independent review."""
    result = await _validate_correctness(
        config, backend, workspace, oracle, artifact_dir, module_name=module_name
    )
    if config.judge is not None:
        from .judge import review_candidate  # noqa: PLC0415

        diagnostic = await review_candidate(
            config,
            backend,
            workspace,
            artifact_dir,
            module_name=module_name,
            tests_passed=result.ok,
        )
        if diagnostic is not None:
            return ValidationResult(
                False, diagnostic, result.output, result.output_dtype, result.metrics
            )
    return result


async def _validate_correctness(
    config: RunConfig,
    backend: ExecutionBackend,
    workspace: str,
    oracle: OracleResult,
    artifact_dir: Path,
    *,
    module_name: str = "candidate.py",
) -> ValidationResult:
    """Require every configured workload to pass, with one report per revision.

    Reference/infrastructure failures propagate rather than triggering candidate repair.
    The primary workload remains mandatory for backward-compatible configurations.
    """
    if not config.arena.correctness_tests:
        return await _validate_single_candidate(
            config, backend, workspace, oracle, artifact_dir, module_name=module_name
        )
    from .execution import put_bytes  # noqa: PLC0415

    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = [
        {
            "id": "primary",
            "dataset": config.kernel.validation_dataset,
            "status": "not_run",
            "reason": "not reached",
        }
    ]
    rows.extend(
        {"id": test.id, "dataset": test.dataset, "status": "not_run", "reason": "not reached"}
        for test in config.arena.correctness_tests
    )
    started = time.monotonic()
    primary = None
    stop_reason = None
    runtime_failures = 0
    try:
        for index, row in enumerate(rows):
            remaining = config.arena.suite_timeout_s - (time.monotonic() - started)
            if stop_reason or remaining <= 0:
                row["reason"] = stop_reason or "suite execution budget exhausted"
                continue
            case_config = config.model_copy(deep=True)
            case_config.arena.correctness_tests = []
            case_oracle = oracle
            case_dir = artifact_dir / row["id"]
            case_dir.mkdir(parents=True, exist_ok=True)
            if index:
                test = config.arena.correctness_tests[index - 1]
                case_config = case_config.validated_update(
                    kernel=case_config.kernel.validated_update(validation_dataset=test.dataset),
                    oracle=test.oracle,
                    measure=case_config.measure.validated_update(
                        evaluation_dataset=test.dataset,
                        performance_dataset="default",
                        evaluation_oracle=None,
                        performance_oracle=None,
                    ),
                )
                case_config.arena.timeout_s = min(test.timeout_s, remaining)
                case_config.arena.input_check.enabled = True
                if test.input_contract is not None:
                    case_config.arena.input_check.contracts[test.dataset] = test.input_contract
                # References are rebuilt by the trusted harness, never by the candidate.
                case_oracle = await build_oracle(case_config, case_dir)
            fixture = fixture_relative_path(case_config)
            if fixture is not None:
                assert case_config.oracle.input_fixture is not None
                await put_bytes(
                    backend,
                    workspace,
                    fixture,
                    case_config.resolve_project_path(case_config.oracle.input_fixture).read_bytes(),
                )
            remaining = config.arena.suite_timeout_s - (time.monotonic() - started)
            if remaining <= 0:
                row["reason"] = "suite execution budget exhausted during reference preparation"
                continue
            case_config.arena.timeout_s = min(case_config.arena.timeout_s, remaining)
            result = await _validate_single_candidate(
                case_config, backend, workspace, case_oracle, case_dir, module_name=module_name
            )
            if index == 0:
                primary = result
            row.update(status="passed" if result.ok else "failed", reason="")
            if result.diagnostic:
                row["reason"] = result.diagnostic.for_agent()
                row["diagnostic"] = result.diagnostic.to_dict()
                if result.diagnostic.gate in {"write", "compile"}:
                    stop_reason = "candidate could not be loaded; repair required"
                if result.diagnostic.gate == "runtime":
                    runtime_failures += 1
                    if runtime_failures >= 2:
                        stop_reason = "repeated execution failures; repair required"
            row["metrics"] = result.metrics
    except Exception as exc:
        row["status"] = "inconclusive"
        row["reason"] = f"evaluation interrupted: {type(exc).__name__}: {exc}"
        for pending in rows:
            if pending["status"] == "not_run":
                pending["reason"] = "evaluation interrupted by reference or infrastructure failure"
        raise
    finally:
        (artifact_dir / "suite.json").write_text(json.dumps(rows, indent=2) + "\n")
    ok = all(row["status"] == "passed" for row in rows)
    summary = "\n".join(
        f"{row['id']} (dataset={row['dataset']}): {row['status']}"
        + (f" — {row['reason']}" if row["status"] == "not_run" else "")
        for row in rows
    )
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("passed", "failed", "not_run")
    }
    failures = [row for row in rows if row["status"] == "failed"]
    details = "\n\n".join(f"{row['id']}: {row['reason']}" for row in failures[:3])
    if len(failures) > 3:
        details += "\nAdditional diagnostics are saved in suite.json."
    summary = f"Counts: {counts}\n{summary}\n\nFailure diagnostics:\n{details}"
    diagnostic = (
        None
        if ok
        else Diagnostic(
            gate="correctness_suite", message="All required tests must pass.\n" + summary
        )
    )
    return ValidationResult(
        ok,
        diagnostic,
        primary.output if primary else None,
        primary.output_dtype if primary else "",
        primary.metrics if primary else None,
    )


async def _validate_single_candidate(
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
    input_contract = oracle.input_contract_path
    if input_contract is None and config.oracle.fixture_spec is not None:
        rebuilt = await build_oracle(config, artifact_dir / "fixture-oracle")
        input_contract = rebuilt.input_contract_path
    if config.arena.input_check.enabled and input_contract is None:
        from .c_inputs import build_input_contract  # noqa: PLC0415

        # Resumed runs reconstruct OracleResult from saved outputs. Rebuild the
        # independent input fixture rather than silently skipping this gate.
        supplied = config.arena.input_check.contracts.get(config.kernel.validation_dataset)
        if supplied is not None:
            from .input_contract import load_contract  # noqa: PLC0415

            input_contract = config.resolve_project_path(supplied)
            _, metadata = load_contract(input_contract)
            if metadata.get("dataset") != config.kernel.validation_dataset:
                raise ValueError("configured input contract has the wrong dataset")
        else:
            input_contract = await build_input_contract(config, artifact_dir / "input-contract")
    output, output_dtype, diagnostic = await execute_candidate(
        config,
        backend,
        workspace,
        module_name,
        precision="fp64",
        device="cpu",
        artifact_path=artifact_dir / "fp64.npy",
        input_contract=input_contract
        if config.arena.input_check.enabled or config.oracle.fixture_spec is not None
        else None,
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
    input_contract = None
    if config.arena.input_check.enabled or config.oracle.fixture_spec is not None:
        from .c_inputs import build_input_contract  # noqa: PLC0415

        supplied = config.arena.input_check.contracts.get(config.kernel.validation_dataset)
        if supplied is not None:
            from .input_contract import load_contract  # noqa: PLC0415

            input_contract = config.resolve_project_path(supplied)
            _, metadata = load_contract(input_contract)
            if metadata.get("dataset") != config.kernel.validation_dataset:
                raise ValueError("configured input contract has the wrong dataset")
        else:
            input_contract = await build_input_contract(config, artifact_dir / "input-contract")
    base, _, diagnostic = await execute_candidate(
        config,
        backend,
        base_workspace,
        base_module,
        precision="fp32",
        device="cpu",
        artifact_path=artifact_dir / "base-fp32.npy",
        input_contract=input_contract,
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
        input_contract=input_contract,
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
