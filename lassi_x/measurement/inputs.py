"""Stage, capture, and independently verify inputs for every measurement cell."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from ..c_inputs import input_contract_for_dataset
from ..execution import fetch_bytes, put_bytes
from ..input_contract import compare_input_arrays, load_contract
from ..types import Status

if TYPE_CHECKING:
    from ..config import RunConfig
    from ..execution import ExecutionBackend
    from ..types import Measurement
    from ..validation import OracleResult


@dataclass
class MeasurementInputCheck:
    contract: Path
    snapshot: str
    report: Path
    precision: str
    config: RunConfig


async def stage_measurement_input_check(
    config: RunConfig,
    oracle: OracleResult,
    execution: ExecutionBackend,
    workspace: str,
    *,
    precision: str,
    artifact: Path,
) -> tuple[list[str], MeasurementInputCheck | None]:
    if not config.arena.input_check.enabled:
        return [], None
    contract = await input_contract_for_dataset(config, oracle, config.evaluation_dataset)
    snapshot = f".lassi/input-{uuid.uuid4().hex}.npz"
    remote = ".lassi/measurement-input-contract.npz"
    await put_bytes(execution, workspace, remote, contract.read_bytes())
    # Standalone workers run in SDK environments without the harness package.
    await put_bytes(
        execution,
        workspace,
        "lassi_input_contract.py",
        (Path(__file__).resolve().parents[1] / "input_contract.py").read_bytes(),
    )
    check = config.arena.input_check
    return [
        "--input-contract",
        remote,
        "--input-snapshot",
        snapshot,
        "--input-bindings",
        json.dumps(check.bindings),
        "--input-rtol",
        str(check.rtol),
        "--input-atol",
        str(check.atol),
    ], MeasurementInputCheck(contract, snapshot, artifact, precision, config)


async def verify_measurement_input_check(
    measurement: Measurement,
    check: MeasurementInputCheck | None,
    execution: ExecutionBackend,
    workspace: str,
) -> Measurement:
    if check is None:
        return measurement
    try:
        data = await fetch_bytes(execution, workspace, check.snapshot)
        check.report.parent.mkdir(parents=True, exist_ok=True)
        check.report.with_suffix(".npz").write_bytes(data)
        with np.load(check.report.with_suffix(".npz"), allow_pickle=False) as archive:
            actual = {name: archive[name] for name in archive.files}
        expected, metadata = load_contract(check.contract)
        policy = check.config.arena.input_check
        report = compare_input_arrays(
            actual,
            expected,
            metadata,
            precision=check.precision,
            bindings=policy.bindings,
            rtol=policy.rtol,
            atol=policy.atol,
        )
        report.update(
            dataset=check.config.evaluation_dataset,
            contract_sha256=hashlib.sha256(check.contract.read_bytes()).hexdigest(),
            snapshot_sha256=hashlib.sha256(data).hexdigest(),
        )
    except Exception as exc:  # noqa: BLE001
        report = {
            "ok": False,
            "errors": [f"input evidence unavailable: {type(exc).__name__}: {exc}"],
        }
    report.update(
        protocol="c-input-parity-v1",
        precision=check.precision,
        dataset=check.config.evaluation_dataset,
        source_sha256=measurement.source_hash,
    )
    check.report.parent.mkdir(parents=True, exist_ok=True)
    check.report.write_text(json.dumps(report, indent=2) + "\n")
    measurement.input_check = report
    if not report["ok"]:
        measurement.status = Status.CRASHED
        measurement.failure_kind = "inputs"
        measurement.notes = json.dumps(report["errors"])
        measurement.latency_s = None
        measurement.min_s = None
    return measurement
