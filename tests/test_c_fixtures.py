from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml

from lassi_x.candidate_runner import run_module
from lassi_x.config import RunConfig
from lassi_x.execution import LocalExecutionBackend
from lassi_x.input_contract import (
    InputContractError,
    load_contract,
    save_contract,
    supplied_fixture_inputs,
)
from lassi_x.validation import build_oracle, validate_candidate

from .test_config import minimal_config


def setup(tmp_path: Path) -> RunConfig:
    if not shutil.which("gcc"):
        pytest.skip("C compiler unavailable")
    (tmp_path / "tiny.c").write_text("""
#include <stdint.h>
int main(void) {
  float A[2][2];
  int64_t index[2] = {9007199254740993LL, 7};
  int steps = 3;
  for (int i = 0; i < 2; ++i)
    for (int j = 0; j < 2; ++j) A[i][j] = (float)(i * 2 + j + 1) / 3;
  /* COMPUTE */
  for (int step = 0; step < steps; ++step)
    for (int i = 0; i < 2; ++i)
      for (int j = 0; j < 2; ++j) A[i][j] += 1;
  /* FINISH */
  return 0;
}
""")
    spec = {
        "before": "  /* COMPUTE */",
        "after": "  /* FINISH */",
        "inputs": {
            "A": {"argument": "a", "access": "read_write"},
            "index": {"argument": "index", "access": "read_only"},
            "steps": {"argument": "steps", "access": "read_only", "scalar": True},
        },
        "outputs": ["A"],
        "fields": {
            "A": {"expression": "A", "shape": ["2", "2"]},
            "index": {"expression": "index", "shape": ["2"]},
        },
    }
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump(spec))
    data = minimal_config(tmp_path)
    data["kernel"]["validation_dataset"] = "large"
    data["measure"]["evaluation_dataset"] = "large"
    data["oracle"]["fixture_spec"] = "spec.yaml"
    data["oracle"]["build"].insert(1, "-std=c11")
    data["oracle"]["build"].insert(2, "-DLARGE_DATASET")
    return RunConfig.model_validate(data)


def test_capture_executes_c_and_preserves_original_types(tmp_path: Path) -> None:
    config = setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    assert oracle.input_contract_path is not None
    inputs, metadata = load_contract(oracle.input_contract_path)
    assert inputs["A"].dtype == np.dtype("float32")
    assert inputs["A"].shape == (2, 2)
    assert inputs["index"].dtype == np.dtype("int64")
    assert inputs["index"][0] == 9007199254740993
    assert inputs["steps"].shape == ()
    assert metadata["dataset"] == "large"
    expected = inputs["A"].copy()
    for _ in range(3):
        expected += np.float32(1)
    np.testing.assert_array_equal(oracle.values, expected.ravel())
    manifest = json.loads(oracle.input_contract_path.with_name("manifest.json").read_text())
    assert (
        manifest["inputs_sha256"]
        == hashlib.sha256(oracle.input_contract_path.read_bytes()).hexdigest()
    )


@pytest.mark.parametrize("precision", ["fp64", "fp32", "fp16", "bf16"])
def test_direct_forward_never_calls_candidate_builder_and_gets_fresh_inputs(
    tmp_path: Path, precision: str
) -> None:
    config = setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    candidate = tmp_path / "candidate.py"
    candidate.write_text("""
import torch
def build_inputs(**kwargs): raise AssertionError("candidate owns no inputs")
def forward(a, index, steps):
    assert index.dtype == torch.int64
    assert index[0].item() == 9007199254740993
    assert isinstance(steps, int) and steps == 3
    for _ in range(steps): a.add_(1)
    return a
""")
    first, _ = run_module(
        candidate, device="cpu", precision=precision, input_contract=oracle.input_contract_path
    )
    second, _ = run_module(
        candidate, device="cpu", precision=precision, input_contract=oracle.input_contract_path
    )
    np.testing.assert_array_equal(first, second)


def test_read_only_mutation_rejected(tmp_path: Path) -> None:
    config = setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    candidate = tmp_path / "candidate.py"
    candidate.write_text("def forward(a, index, steps):\n    index.add_(1)\n    return a\n")
    with pytest.raises(InputContractError, match="read-only"):
        run_module(
            candidate, device="cpu", precision="fp64", input_contract=oracle.input_contract_path
        )


def test_alternate_inputs_are_imported_before_c_computation(tmp_path: Path) -> None:
    config = setup(tmp_path)
    original = asyncio.run(build_oracle(config, tmp_path / "original"))
    assert original.input_contract_path is not None
    arrays, metadata = load_contract(original.input_contract_path)
    arrays["A"] = np.full((2, 2), 5, dtype=np.float32)
    arrays["steps"] = np.asarray(2, dtype=np.int32)
    alternate = tmp_path / "alternate.npz"
    save_contract(alternate, arrays, metadata)
    config.oracle.input_fixture = alternate
    oracle = asyncio.run(build_oracle(config, tmp_path / "alternate"))
    np.testing.assert_array_equal(oracle.values, np.full(4, 7))
    arrays["A"] = arrays["A"].reshape(4)
    save_contract(alternate, arrays, metadata)
    with pytest.raises(RuntimeError, match="execution failed"):
        asyncio.run(build_oracle(config, tmp_path / "bad-shape"))


def test_fixture_checksum_is_verified(tmp_path: Path) -> None:
    config = setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    assert oracle.input_contract_path is not None
    arrays, metadata = load_contract(oracle.input_contract_path)
    arrays["A"][0, 0] += 1
    payload: dict[str, Any] = {**arrays, "__metadata__": np.asarray(json.dumps(metadata))}
    np.savez(oracle.input_contract_path, **payload)
    with pytest.raises(InputContractError, match="checksum"):
        load_contract(oracle.input_contract_path)


def test_polybench_structural_instrumentation(tmp_path: Path) -> None:
    config = setup(tmp_path)
    repo = Path(__file__).resolve().parents[1]
    root = repo / "benchmarks/polybench"
    reference = root / "linear-algebra/blas/gemm/gemm.c"
    spec = {
        "inputs": {
            name: {"argument": name.lower(), "access": access}
            for name, access in [
                ("A", "read_only"),
                ("B", "read_only"),
                ("C", "read_write"),
                ("alpha", "read_only"),
                ("beta", "read_only"),
            ]
        },
        "outputs": ["C"],
    }
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump(spec))
    config.kernel.reference = reference
    config.oracle.build = [
        "gcc",
        "-std=c11",
        "-DMINI_DATASET",
        "-DDATA_TYPE_IS_DOUBLE",
        "-I" + str(root / "utilities"),
        "{reference}",
        str(root / "utilities/polybench.c"),
        "-lm",
        "-o",
        "{oracle_dir}/tiny",
    ]
    oracle = asyncio.run(build_oracle(config, tmp_path / "gemm"))
    assert oracle.input_contract_path is not None
    arrays, _ = load_contract(oracle.input_contract_path)
    expected = arrays["beta"] * arrays["C"] + arrays["alpha"] * (arrays["A"] @ arrays["B"])
    np.testing.assert_allclose(oracle.values, expected.ravel(), rtol=1e-12)


def test_one_cast_uses_initialized_float_storage(tmp_path: Path) -> None:
    config = setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    assert oracle.input_contract_path is not None
    arrays, _ = load_contract(oracle.input_contract_path)
    args, _ = supplied_fixture_inputs(oracle.input_contract_path, device="cpu", dtype=torch.float16)
    assert args["a"].dtype == torch.float16
    np.testing.assert_array_equal(args["a"].numpy(), arrays["A"].astype(np.float16))


def test_validation_uses_fixture_even_without_legacy_parity_opt_in(tmp_path: Path) -> None:
    config = setup(tmp_path)
    assert not config.arena.input_check.enabled
    root = tmp_path / "workspaces"
    workspace = root / "candidate"
    workspace.mkdir(parents=True)
    (workspace / "candidate.py").write_text("""
def forward(a, index, steps):
    # Reproduce C's float32 storage rounding after each update, then widen back.
    for _ in range(steps): a = (a.float() + 1).to(a.dtype)
    return a
""")
    backend = LocalExecutionBackend(root, "fixture-test")
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    result = asyncio.run(
        validate_candidate(config, backend, "candidate", oracle, tmp_path / "validation")
    )
    assert result.ok, result.diagnostic
    # A reconstructed OracleResult must not fall back to candidate-owned inputs.
    oracle.input_contract_path = None
    result = asyncio.run(
        validate_candidate(config, backend, "candidate", oracle, tmp_path / "resumed")
    )
    assert result.ok, result.diagnostic
