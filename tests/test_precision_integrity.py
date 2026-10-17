from __future__ import annotations

import json
import subprocess
import sys
from typing import TYPE_CHECKING

import numpy as np

from lassi_x.measurement.common import _attach_precision_evidence
from lassi_x.types import Measurement, Status

if TYPE_CHECKING:
    from pathlib import Path


def point() -> Measurement:
    return Measurement(
        kernel="k",
        candidate_id="c1",
        variant_id="v",
        backend="a100",
        precision="fp16",
        compensation="none",
        status=Status.OK,
        module_path="candidate.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        source_hash="source",
        latency_s=1.0,
        relative_l2=0.001,
        error_metric="relative_l2",
        evaluation_output_checked=True,
        evaluation_output_finite=True,
        evaluation_semantic_verified=True,
        accuracy_source="timed_iteration",
        timing_protocol="architectural-single-call-v1",
    )


def test_old_results_preserved_but_unverified() -> None:
    old = point().to_dict()
    for key in list(old):
        if key.startswith("precision_") or key == "arithmetic_policy":
            old.pop(key)
    restored = Measurement.from_dict(old)
    assert restored.status == Status.OK
    assert restored.relative_l2 == 0.001
    assert restored.precision_verdict == "unverified"
    assert not restored.frontier_eligible


def test_mixed_evidence_is_policy_bound_and_roundtrips_labels() -> None:
    record = point()
    proof = {
        "source_hash": "source",
        "dtype_audit": {
            "protocol": "executed-dtype-v4",
            "requested_precision": "fp16",
            "dataset": "default",
            "source_hash": "source",
            "complete": True,
            "passed": True,
            "arithmetic_policy": "mixed",
            "arithmetic_class": "mixed_accumulation",
            "observed_tensor_dtypes": ["torch.float16", "torch.float32"],
            "wider_operations": [{"operation": "aten.sum.default"}],
            "violations": [],
        },
    }
    _attach_precision_evidence(record, proof)
    assert not record.precision_eligible
    record.arithmetic_policy = "mixed"
    _attach_precision_evidence(record, proof)
    assert record.precision_eligible
    restored = Measurement.from_dict(record.to_dict())
    assert restored.arithmetic_class == "mixed_accumulation"
    assert restored.wider_operations == [{"operation": "aten.sum.default"}]
    assert restored.implicit_accumulator_precision == "unverified"


def test_worker_uses_frozen_inputs_not_repair_builder(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.py"
    baseline.write_text(
        "import torch\n"
        "def build_inputs(device='cpu', dtype=torch.float64):\n"
        "    return (torch.ones(4,device=device,dtype=dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def forward(self,x): return x+x\n"
        "def make_model(): return Model()\n"
    )
    candidate = tmp_path / "candidate.py"
    candidate.write_text(baseline.read_text().replace("torch.ones(4,", "99*torch.ones(4,"))
    oracle = tmp_path / "oracle.npy"
    np.save(oracle, np.full(4, 2.0))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lassi_x.precision_audit_worker",
            "--module",
            str(candidate),
            "--audit-baseline",
            str(baseline),
            "--oracle",
            str(oracle),
            "--device",
            "cpu",
            "--precision",
            "fp16",
            "--warmup",
            "1",
            "--iterations",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 0, payload
    assert payload["dtype_audit"]["input_contract"] == "frozen_baseline"
    assert payload["dtype_audit"]["passed"] is True
    assert payload["equivalent"] is True


def test_bound_evidence_required_for_ranking_and_stability() -> None:
    record = point()
    proof = {
        "source_hash": "source",
        "dtype_audit": {
            "protocol": "executed-dtype-v3",
            "requested_precision": "fp16",
            "dataset": "default",
            "source_hash": "source",
            "complete": True,
            "passed": True,
            "violations": [],
        },
    }
    _attach_precision_evidence(record, proof)
    assert record.frontier_eligible
    assert record.stable_success
    record.relative_l2 = 0.05
    assert not record.stable_success
    proof["source_hash"] = "changed"
    _attach_precision_evidence(record, proof)
    assert record.precision_verdict == "unverified"
    assert not record.frontier_eligible


def test_failed_audit_cannot_enter_frontier_even_when_execution_succeeded() -> None:
    record = point()
    _attach_precision_evidence(
        record,
        {
            "source_hash": "source",
            "dtype_audit": {
                "protocol": "executed-dtype-v3",
                "requested_precision": "fp16",
                "dataset": "default",
                "source_hash": "source",
                "complete": True,
                "passed": False,
                "violations": ["FP32 arithmetic"],
            },
        },
    )
    assert record.status == Status.OK  # Keep the observed execution outcome.
    assert record.precision_verdict == "failed"
    assert not record.frontier_eligible
    assert not record.stable_success


def test_worker_checks_actual_timed_path(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    candidate.write_text(
        "import torch\n"
        "def build_inputs(device='cpu', dtype=torch.float64):\n"
        "    return (torch.ones(4,device=device,dtype=dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def __init__(self):\n"
        "        super().__init__(); self.calls=0\n"
        "    def forward(self,x):\n"
        "        self.calls+=1\n"
        "        return x+x if self.calls<=2 else (x.float()+x.float()).to(x.dtype)\n"
        "def make_model(): return Model()\n"
    )
    oracle = tmp_path / "oracle.npy"
    np.save(oracle, np.full(4, 2.0))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lassi_x.measure_worker",
            "--module",
            str(candidate),
            "--oracle",
            str(oracle),
            "--device",
            "cpu",
            "--precision",
            "fp16",
            "--warmup",
            "2",
            "--iterations",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode != 0
    assert payload["phase"] == "precision_policy"
    assert payload["dtype_audit"]["protocol"] == "executed-dtype-v4"
    assert payload["dtype_audit"]["forward_calls"] == 3
    assert payload["dtype_audit"]["passed"] is False


def test_worker_keeps_valid_constants_and_checks_every_output(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.py"
    template = (
        "import torch\n"
        "def build_inputs(device='cpu', dtype=torch.float64):\n"
        "    return (torch.ones(4,device=device,dtype=dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self.register_buffer('c',torch.tensor(2.,dtype=torch.float64))\n"
        "    def forward(self,x): return OUTPUT\n"
        "def make_model(): return Model()\n"
    )
    oracle = tmp_path / "oracle.npy"
    np.save(oracle, np.full(4, 2.0))
    command = [
        sys.executable,
        "-m",
        "lassi_x.measure_worker",
        "--module",
        str(candidate),
        "--oracle",
        str(oracle),
        "--device",
        "cpu",
        "--precision",
        "fp16",
        "--warmup",
        "0",
        "--iterations",
        "1",
    ]
    candidate.write_text(template.replace("OUTPUT", "self.c*x"))
    good = subprocess.run(command, capture_output=True, text=True, check=False)
    assert good.returncode == 0, good.stdout + good.stderr
    proof = json.loads(good.stdout)["dtype_audit"]
    assert proof["passed"] and proof["complete"]
    candidate.write_text(template.replace("OUTPUT", "(self.c*x, x.float())"))
    bad = subprocess.run(command, capture_output=True, text=True, check=False)
    assert bad.returncode != 0
    assert json.loads(bad.stdout)["dtype_audit"]["passed"] is False
