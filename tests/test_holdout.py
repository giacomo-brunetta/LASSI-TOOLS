"""Holdout harness checks. These do not participate in numerical repair feedback."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from lassi_x.holdout import (
    c_output,
    evaluate,
    injected_reference,
    input_values,
    make_case,
    metrics,
    prepare,
    sha,
    write,
)
from lassi_x.input_contract import save_contract

SPEC = Path(__file__).resolve().parents[1] / "experiments/holdout-validation/accuracy_holdout.json"


def test_preparation_binds_final_target_measurement_without_importing_sources(
    tmp_path: Path,
) -> None:
    import yaml  # noqa: PLC0415

    campaign = tmp_path / "campaign"
    trial = campaign / "sol/direct-dft/c1-fp16"
    trial.mkdir(parents=True)
    baseline = tmp_path / "baseline"
    baseline.mkdir()
    for path in (baseline / "candidate.py", trial / "candidate.py"):
        path.write_text("raise AssertionError('Preparation must not import candidate code')\n")
    source = tmp_path / "direct-dft.c"
    source.write_text("int main(void) {return 0;}\n")
    contract = tmp_path / "contract.npz"
    values = {"signal": np.arange(4, dtype=np.float64)}
    save_contract(
        contract,
        values,
        {
            "kernel": "direct-dft",
            "required": ["signal"],
            "dataset": "large",
            "source_sha256": sha(source),
        },
    )
    schema = [
        {"argument": "signal", "kind": "tensor", "shape": [4], "stride": [1], "integer_dtype": None}
    ]
    np.savez(
        baseline / "c-inputs.npz",
        signal=values["signal"],
        __lassi_input_schema__=np.asarray(json.dumps(schema)),
    )
    write(baseline / "baseline.json", {"source_sha256": sha(baseline / "candidate.py")})
    write(
        trial / "repair.json",
        {
            "row": {"model": "sol", "kernel": "direct-dft", "candidate": "c1", "precision": "fp16"},
            "variant": {
                "recovered": True,
                "module_path": str(trial / "candidate.py"),
                "target_measurements": [
                    {"precision": "fp16", "status": "crashed", "source_hash": "old-attempt"},
                    {
                        "precision": "fp16",
                        "status": "ok",
                        "source_hash": sha(trial / "candidate.py"),
                    },
                ],
            },
            "baseline_record": str(baseline / "baseline.json"),
        },
    )
    config = {
        "project": {"root": str(tmp_path)},
        "measure": {"evaluation_dataset": "large"},
        "kernel": {"reference": str(source)},
        "arena": {"input_check": {"contracts": {"large": str(contract)}, "bindings": {}}},
        "oracle": {
            "build": ["cc", "{reference}", "-o", "{oracle_dir}/reference"],
            "capture": "stdout",
            "format": "numeric",
        },
    }
    (trial / "config.yaml").write_text(yaml.safe_dump(config))
    output = tmp_path / "freeze"
    prepare(campaign, output, SPEC)
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(manifest["targets"]) == 1
    with pytest.raises(ValueError, match="cannot be overwritten"):
        prepare(campaign, output, SPEC)
    (trial / "candidate.py").write_text("raise AssertionError('changed source')\n")
    with pytest.raises(ValueError, match="does not match its measurements"):
        prepare(campaign, tmp_path / "changed-freeze", SPEC)


def test_spd_cases_preserve_symmetry_and_positive_definiteness() -> None:
    a = np.asarray([[3.0, 1.0], [1.0, 2.0]])
    metadata = {"kernel": "polybench-cholesky", "required": ["A"]}
    for case in json.loads(SPEC.read_text())["cases"]:
        values = make_case({"A": a}, metadata, case)
        assert np.array_equal(values["A"], values["A"].T)
        assert np.linalg.eigvalsh(values["A"]).min() > 0
        assert not np.array_equal(values["A"], a)
    assert np.array_equal(a, [[3, 1], [1, 2]])


def test_dependent_cg_initial_state_is_reestablished() -> None:
    original = {
        "x": np.zeros(8),
        "r": np.ones(8),
        "p": np.ones(8),
        "ap": np.zeros(8),
        "rr": np.asarray(8.0),
    }
    metadata = {"kernel": "poisson-cg", "required": ["r"]}
    case = {"family": "local", "seed": 381, "amount": 0.25}
    values = make_case(original, metadata, case)
    assert np.array_equal(values["p"], values["r"])
    assert values["rr"] == pytest.approx(np.dot(values["r"], values["r"]))
    assert np.array_equal(values["x"], original["x"])
    assert not np.array_equal(values["r"], original["r"])
    repeated = make_case(original, metadata, case)
    assert all(np.array_equal(values[k], repeated[k]) for k in values)


def test_fixed_timestep_does_not_follow_changed_lorenz_state() -> None:
    original = {"state": np.ones((8, 3)), "dt": np.asarray(0.001), "steps": np.asarray(20)}
    metadata = {"kernel": "lorenz-rk4", "required": ["state"], "integer_fields": ["steps"]}
    values = make_case(original, metadata, {"family": "scale", "seed": 731, "amount": 2})
    assert values["state"][0, 0] == 2
    assert values["dt"] == 0.001
    assert values["steps"] == 20


def test_c_output_boundaries_prevent_hiding_wrong_scalar() -> None:
    expected = np.concatenate([np.ones(1000) * 100, [0.1, 42]])
    actual = expected.copy()
    actual[-2] = 0.2
    assert metrics(actual, expected, [1000, 1, 1])["relative_l2"] == pytest.approx(1.0)
    assert metrics(actual, expected, [1002])["relative_l2"] < 0.01
    with pytest.raises(ValueError):
        metrics(actual, expected, [1000])


def test_packed_input_mapping_is_harness_owned() -> None:
    arrays = {"A": np.eye(3), "B": np.ones((3, 3)), "x": np.arange(3)}
    schema = [{"argument": "M", "shape": [2, 3, 3]}, {"argument": "x", "shape": [3]}]
    packed, vector = input_values(arrays, schema, {"kernel": "polybench-gesummv", "bindings": {}})
    assert np.array_equal(packed, np.stack([arrays["A"], arrays["B"]]))
    assert np.array_equal(vector, arrays["x"])
    with pytest.raises(ValueError, match="trusted input binding"):
        input_values(
            arrays, [{"argument": "answer", "shape": [3]}], {"kernel": "direct-dft", "bindings": {}}
        )


def test_science_injection_preserves_computation_and_fixed_parameters() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "benchmarks/scientific/lorenz-rk4.c"
    ).read_text()
    generated, fields = injected_reference(
        source,
        "lorenz-rk4",
        {
            "state": np.ones((8, 3)),
            "dt": np.asarray(0.001),
            "steps": np.asarray(20),
        },
    )
    assert fields == ["state"]
    boundary = source.index("  for (int step =")
    assert generated.endswith(source[boundary:])
    assert generated.count("const double dt = 0.001;") == 1
    assert "dt = lassi_value" not in generated


def test_polybench_components_come_from_c_dump(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import subprocess  # noqa: PLC0415

    text = (
        b"==BEGIN DUMP_ARRAYS==\nbegin dump: a\n1 2\nend   dump: a\n"
        b"begin dump: b\n3\nend   dump: b\n==END DUMP_ARRAYS=="
    )
    monkeypatch.setattr(
        "lassi_x.holdout.run_command", lambda *a: subprocess.CompletedProcess([], 0, b"", text)
    )
    flat, sizes = c_output(
        {"timeout_s": 1, "capture": "stderr", "format": "polybench"},
        tmp_path / "unused",
        [],
        {},
        tmp_path,
    )
    assert np.array_equal(flat, [1, 2, 3])
    assert sizes == [2, 1]


def test_polybench_output_envelope_matches_established_oracle(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import subprocess  # noqa: PLC0415

    from lassi_x.validation import scrape_polybench_dump  # noqa: PLC0415

    # FDTD's C source ends its exported dump after ex, then prints diagnostics.
    text = (
        b"==BEGIN DUMP_ARRAYS==\nbegin dump: ex\n1 2\nend   dump: ex\n"
        b"==END DUMP_ARRAYS==\nbegin dump: ey\n3 4\nend   dump: ey\n"
        b"begin dump: hz\n5 6\nend   dump: hz\n"
    )
    monkeypatch.setattr(
        "lassi_x.holdout.run_command", lambda *a: subprocess.CompletedProcess([], 0, b"", text)
    )
    flat, sizes = c_output(
        {"timeout_s": 1, "capture": "stderr", "format": "polybench"},
        tmp_path / "unused",
        [],
        {},
        tmp_path,
    )
    assert np.array_equal(flat, scrape_polybench_dump(text.decode()))
    assert np.array_equal(flat, [1, 2])
    assert sizes == [2]


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_fixture_overfit_passes_control_but_fails_holdout(tmp_path: Path) -> None:
    """A real tiny C differential test; neither candidate builder may run."""
    pytest.importorskip("torch")
    root = tmp_path / "freeze"
    folder = root / "sol/direct-dft/c1-fp16"
    folder.mkdir(parents=True)
    reference = tmp_path / "reference.c"
    reference.write_text("""#include <stdio.h>
#define SIZE 4
int main(void) {
  double signal[SIZE], real[SIZE];
  for (int i=0; i<SIZE; ++i) signal[i]=i+1;
  for (int k = 0; k < SIZE; ++k) {
    real[k] = signal[k]*2;
  }
  for (int i=0; i<SIZE; ++i) printf("%.17g\\n", real[i]);
  return 0;
}
""")
    prefix = """import torch
def build_inputs(*args, **kwargs):
    raise AssertionError("Candidate builders must never supply holdout inputs")
class Model(torch.nn.Module):
    def forward(self, signal):
"""
    suffix = "\ndef make_model():\n    return Model()\n"
    (folder / "baseline.py").write_text(prefix + "        return signal*2\n" + suffix)
    (folder / "repaired.py").write_text(
        prefix
        + "        return torch.tensor([2,4,6,8], dtype=signal.dtype, device=signal.device)\n"
        + suffix
    )
    save_contract(
        folder / "contract.npz",
        {"signal": np.arange(1, 5, dtype=np.float64)},
        {"kernel": "direct-dft", "required": ["signal"], "dataset": "large"},
    )
    write(
        folder / "schema.json",
        [
            {
                "argument": "signal",
                "kind": "tensor",
                "shape": [4],
                "stride": [1],
                "integer_dtype": None,
            }
        ],
    )
    write(
        folder / "target.json",
        {
            "kernel": "direct-dft",
            "precision": "fp16",
            "bindings": {},
            "reference": str(reference),
            "project": str(tmp_path),
            "timeout_s": 10,
            "build": ["cc", "{reference}", "-o", "{oracle_dir}/reference"],
            "capture": "stdout",
            "format": "numeric",
            "dependencies": {str(reference): sha(reference)},
        },
    )
    write(root / "policy.json", json.loads(SPEC.read_text()))
    write(
        root / "manifest.json",
        {
            "targets": [str((folder / "target.json").relative_to(root))],
            "files": {str(p.relative_to(root)): sha(p) for p in root.rglob("*") if p.is_file()},
        },
    )
    results = tmp_path / "results"
    assert not evaluate(root / "manifest.json", folder / "target.json", results, "cpu")
    report = json.loads((results / "summary.json").read_text())
    assert report["cases"][0]["passed"]
    assert report["holdout_passes"] < report["holdout_cases"]
    assert all(r["baseline_passed"] for r in report["cases"])
    # Immutable source hashes reject drift before another evaluation starts.
    (folder / "repaired.py").write_text("raise RuntimeError('changed')\n")
    with pytest.raises(ValueError, match="artifact changed"):
        evaluate(root / "manifest.json", folder / "target.json", tmp_path / "more", "cpu")
