from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import numpy as np
import pytest
import yaml

from lassi_x.candidate_runner import run_module
from lassi_x.config import RunConfig, TorchBackendConfig
from lassi_x.execution import LocalExecutionBackend
from lassi_x.input_contract import (
    InputContractError,
    compare_input_arrays,
    load_contract,
    save_contract,
)
from lassi_x.measurement import TorchBackend
from lassi_x.types import Measurement, Status
from lassi_x.validation import build_oracle, validate_candidate

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("bad", ["changed", "answer", "extra", "missing", "nan", "shape"])
def test_input_contract_rejects_invalid_inputs(bad: str) -> None:
    expected = {"A": np.arange(6.0).reshape(2, 3)}
    actual = {"A": expected["A"].copy()}
    if bad == "changed":
        actual["A"][0, 0] = 0.1
    elif bad == "answer":
        actual["A"] = expected["A"] ** 2
    elif bad == "extra":
        actual["answer"] = expected["A"] ** 2
    elif bad == "missing":
        actual = {}
    elif bad == "nan":
        actual["A"][0, 0] = np.nan
    else:
        actual["A"] = actual["A"].reshape(3, 2)
    report = compare_input_arrays(actual, expected, {"kernel": "example", "required": ["A"]})
    assert not report["ok"]
    assert report["errors"]


def test_names_bind_to_reference_fields_not_best_matching_values() -> None:
    expected = {"A": np.ones((2, 2)), "B": np.full((2, 2), 2.0)}
    report = compare_input_arrays(
        {"B": expected["A"], "A": expected["B"]},
        expected,
        {"kernel": "example", "required": ["A", "B"]},
    )
    assert not report["ok"]


def test_integer_inputs_cannot_use_floating_tolerances() -> None:
    report = compare_input_arrays(
        {"seq": np.asarray([1.001])},
        {"seq": np.asarray([1.0])},
        {"kernel": "polybench-nussinov", "required": ["seq"], "integer_fields": ["seq"]},
        rtol=1.0,
        atol=1.0,
    )
    assert not report["ok"]


def test_zero_workspaces_must_be_exactly_zero() -> None:
    report = compare_input_arrays(
        {"tmp": np.asarray([1e-300])},
        {"tmp": np.asarray([0.0])},
        {"kernel": "example", "required": []},
    )
    assert not report["ok"]


def test_batched_stencil_and_explicit_transpose_bindings() -> None:
    expected = {"A": np.arange(6.0).reshape(2, 3)}
    metadata = {"kernel": "example", "required": ["A"]}
    assert compare_input_arrays({"A": expected["A"][None, None]}, expected, metadata)["ok"]
    assert compare_input_arrays(
        {"weight": expected["A"].T}, expected, metadata, bindings={"weight": "A.T"}
    )["ok"]
    assert not compare_input_arrays({"weight": expected["A"].T}, expected, metadata)["ok"]


def test_failed_input_check_runs_before_forward(tmp_path: Path) -> None:
    module = tmp_path / "candidate.py"
    module.write_text(
        "import torch\n"
        "def build_inputs(device, dtype):\n"
        "    return (torch.tensor([999.], device=device, dtype=dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def forward(self, x):\n"
        "        raise AssertionError('forward must not run')\n"
        "def make_model(): return Model()\n"
    )
    contract = tmp_path / "inputs.npz"
    save_contract(contract, {"x": np.asarray([1.0])}, {"kernel": "example", "required": ["x"]})
    with pytest.raises(InputContractError, match="value mismatch"):
        run_module(module, device="cpu", precision="fp64", input_contract=contract)


C_REFERENCE = r"""
#include <stdio.h>
#define N 3
#define POLYBENCH_ARRAY(a) a
#define POLYBENCH_1D_ARRAY_DECL(a, t, N, n) t a[N]
static void init_array(int n, double x[N]) {
    for (int i=0; i<n; ++i) x[i] = i+1;
}
static void kernel_identity(int n, double x[N]) { }
int main(int argc, char **argv) {
    int n = N;
    POLYBENCH_1D_ARRAY_DECL(x, double, N, n);
    init_array(n, POLYBENCH_ARRAY(x));
    kernel_identity(n, POLYBENCH_ARRAY(x));
    FILE *f = fopen(argv[1], "w");
    for (int i=0; i<n; ++i) fprintf(f, "%.17g\n", x[i]);
    fclose(f);
    return 0;
}
"""


def test_gate_rejects_wrong_inputs_even_when_outputs_match(tmp_path: Path) -> None:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    data = minimal_config(tmp_path)
    data["arena"] = {"input_check": {"enabled": True}}
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    root = tmp_path / "workspaces"
    for name, values in (
        ("good", "[1., 2., 3.]"),
        ("bad", "[8., 9., 10.]"),
        ("tampered", "[8., 9., 10.]"),
    ):
        workspace = root / name
        workspace.mkdir(parents=True)
        (workspace / "candidate.py").write_text(
            "import torch\n"
            "def build_inputs(device, dtype):\n"
            f"    return (torch.tensor({values}, device=device, dtype=dtype),)\n"
            "class Model(torch.nn.Module):\n"
            "    def forward(self, x):\n"
            "        return torch.tensor([1., 2., 3.], dtype=x.dtype)\n"
            "def make_model(): return Model()\n"
        )
        if name == "tampered":
            # A worker-side decision alone is insufficient: changing the staged
            # fixture must not change the authoritative harness-side comparison.
            with (workspace / "candidate.py").open("a") as stream:
                stream.write(
                    "import numpy as np\nfrom pathlib import Path\n"
                    "p = Path(__file__).parent / '.lassi/trusted-input-contract.npz'\n"
                    "with np.load(p, allow_pickle=False) as z:\n"
                    "    a = {k: z[k] for k in z.files}\n"
                    "a['x'] = np.array([8., 9., 10.])\n"
                    "np.savez(p, **a)\n"
                )
    backend = LocalExecutionBackend(root, "test-input-gate")
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    assert oracle.input_contract_path is not None
    arrays, _ = load_contract(oracle.input_contract_path)
    assert arrays["x"].tolist() == [1.0, 2.0, 3.0]
    good = asyncio.run(validate_candidate(config, backend, "good", oracle, tmp_path / "good"))
    bad = asyncio.run(validate_candidate(config, backend, "bad", oracle, tmp_path / "bad"))
    assert good.ok
    assert not bad.ok
    assert bad.diagnostic is not None and bad.diagnostic.gate == "inputs"
    assert not (tmp_path / "bad/fp64.npy").exists()
    report = json.loads((tmp_path / "bad/fp64.inputs.json").read_text())
    assert not report["ok"]
    tampered = asyncio.run(
        validate_candidate(config, backend, "tampered", oracle, tmp_path / "tampered")
    )
    assert not tampered.ok
    assert tampered.diagnostic is not None and tampered.diagnostic.gate == "inputs"
    # Resumed runs must enforce the gate even without an in-memory contract path.
    oracle.input_contract_path = None
    resumed = asyncio.run(validate_candidate(config, backend, "bad", oracle, tmp_path / "resumed"))
    assert not resumed.ok
    assert resumed.diagnostic is not None and resumed.diagnostic.gate == "inputs"


@pytest.mark.parametrize("precision", ["fp32", "fp16", "bf16"])
def test_one_cast_input_policy_is_exact_at_target_precision(precision: str) -> None:
    from lassi_x.input_contract import round_input_values  # noqa: PLC0415

    reference = np.asarray([1.1, 2.2, 3.3])
    rounded = round_input_values(reference, precision)
    metadata = {"kernel": "example", "required": ["x"]}
    assert compare_input_arrays({"x": rounded}, {"x": reference}, metadata, precision=precision)[
        "ok"
    ]
    assert not compare_input_arrays(
        {"x": reference}, {"x": reference}, metadata, precision=precision
    )["ok"]
    wrong = rounded.copy()
    wrong[0] = np.nextafter(wrong[0], np.inf)
    assert not compare_input_arrays(
        {"x": wrong}, {"x": reference}, metadata, precision=precision, rtol=1.0
    )["ok"]


@pytest.mark.parametrize("precision", ["fp64", "fp32", "fp16", "bf16"])
def test_every_measurement_and_repair_rechecks_actual_inputs(
    tmp_path: Path, precision: str
) -> None:
    (tmp_path / "tiny.c").write_text(C_REFERENCE.replace("i+1", "1.1*(i+1)"))
    data = minimal_config(tmp_path)
    data["arena"] = {"input_check": {"enabled": True}}
    data["measure"].update(warmup=0, iterations=1)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(config_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    module = tmp_path / "candidate.py"
    source = (
        "import torch\n"
        "def build_inputs(device, dtype):\n"
        "    x = torch.tensor([1.1, 2.2, 3.3], dtype=torch.float64, device=device)\n"
        "    return (x.to(dtype),)\n"
        "class Model(torch.nn.Module):\n"
        "    def forward(self, x): return x\n"
        "def make_model(): return Model()\n"
    )
    module.write_text(source)
    spec = TorchBackendConfig(type="torch", name="cpu", device="cpu", precisions=[precision])
    if precision in {"fp16", "bf16"}:
        baseline = tmp_path / "frozen-base.py"
        baseline.write_text(source)
        spec.precision_audit_reference = baseline
    backend = TorchBackend(spec, LocalExecutionBackend(tmp_path / "remote", "cpu"), "cpu")

    def measure() -> Measurement:
        return asyncio.run(
            backend.measure(
                config,
                oracle,
                module,
                candidate_id="c1",
                variant_id="same-repair-workspace",
                precision=precision,
                compensation="none",
            )
        )

    good = measure()
    assert good.status == Status.OK, good.notes
    assert good.input_check["ok"]
    assert good.input_check["precision"] == precision
    # A later repair changes only its builder. Reusing the same variant/workspace
    # must not reuse the earlier successful input evidence.
    module.write_text(source.replace("[1.1, 2.2, 3.3]", "[8., 9., 10.]"))
    bad = measure()
    assert bad.status == Status.CRASHED, bad.notes
    assert bad.failure_kind == "inputs"
    assert not bad.input_check["ok"]
    assert bad.latency_s is None


def test_fp32_repair_collapse_also_checks_the_builders(tmp_path: Path) -> None:
    from lassi_x.validation import validate_fp32_collapse  # noqa: PLC0415

    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    data = minimal_config(tmp_path)
    data["arena"] = {"input_check": {"enabled": True}}
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    root = tmp_path / "workspaces"
    for name, values in (("base", "[1., 2., 3.]"), ("repair", "[8., 9., 10.]")):
        workspace = root / name
        workspace.mkdir(parents=True)
        (workspace / "candidate.py").write_text(
            "import torch\n"
            "def build_inputs(device, dtype):\n"
            f"    return (torch.tensor({values},device=device,dtype=dtype),)\n"
            "class Model(torch.nn.Module):\n"
            "    def forward(self, x): return torch.tensor([1.,2.,3.],dtype=x.dtype)\n"
            "def make_model(): return Model()\n"
        )
    result = asyncio.run(
        validate_fp32_collapse(
            config, LocalExecutionBackend(root, "test"), "base", "repair", tmp_path / "artifacts"
        )
    )
    assert not result.ok
    assert result.diagnostic is not None and result.diagnostic.gate == "inputs"


def test_evaluation_profile_gets_its_own_c_inputs(tmp_path: Path) -> None:
    from lassi_x.c_inputs import input_contract_for_dataset  # noqa: PLC0415

    source = C_REFERENCE.replace(
        "#define N 3", "#ifdef SMALL_DATASET\n#define N 5\n#else\n#define N 3\n#endif"
    )
    (tmp_path / "tiny.c").write_text(source)
    data = minimal_config(tmp_path)
    data["arena"] = {"input_check": {"enabled": True}}
    data["kernel"]["validation_dataset"] = "mini"
    data["measure"]["evaluation_dataset"] = "mini"
    data["oracle"]["build"].insert(1, "-DMINI_DATASET")
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    assert oracle.input_contract_path is not None
    mini, _ = load_contract(oracle.input_contract_path)
    small_path = asyncio.run(input_contract_for_dataset(config, oracle, "small"))
    small, metadata = load_contract(small_path)
    assert mini["x"].shape == (3,)
    assert small["x"].shape == (5,)
    assert metadata["dataset"] == "small"
    assert asyncio.run(input_contract_for_dataset(config, oracle, "small")) == small_path


def test_missing_worker_input_evidence_cannot_pass(tmp_path: Path) -> None:
    from lassi_x.measurement.inputs import (  # noqa: PLC0415
        MeasurementInputCheck,
        verify_measurement_input_check,
    )

    data = minimal_config(tmp_path)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    sample = Measurement(
        kernel="tiny",
        candidate_id="c1",
        variant_id="v",
        backend="native",
        precision="fp16",
        compensation="none",
        status=Status.OK,
        module_path="candidate.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        latency_s=0.001,
    )
    check = MeasurementInputCheck(
        tmp_path / "contract.npz", "missing.npz", tmp_path / "report.json", "fp16", config
    )
    result = asyncio.run(
        verify_measurement_input_check(
            sample, check, LocalExecutionBackend(tmp_path / "workspaces", "test"), "w"
        )
    )
    assert result.status == Status.CRASHED
    assert result.failure_kind == "inputs"
    assert result.latency_s is None
