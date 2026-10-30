"""Check independent input coverage and legacy variadic input binding."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

SCRIPT = Path(__file__).resolve().parents[1] / "experiments/holdout-validation/run_fp64_holdout.py"
spec = importlib.util.spec_from_file_location("fp64_holdout", SCRIPT)
holdout = importlib.util.module_from_spec(spec)
spec.loader.exec_module(holdout)


def test_twenty_distinct_inputs_even_for_small_sparse_fields():
    original = {"signal": np.arange(4, dtype=float)}
    metadata = dict(kernel="direct-dft", required=["signal"])
    values = [holdout.make_case(original, metadata, c)["signal"] for c in holdout.cases()]
    assert len(values) == 20
    assert len({v.tobytes() for v in values}) == 20
    assert all(not np.array_equal(v, original["signal"]) for v in values)


def test_integer_cases_preserve_discrete_domains_and_change_input():
    for kernel, key, shape in [
        ("polybench-nussinov", "seq", (30,)),
        ("polybench-floyd-warshall", "path", (12, 12)),
    ]:
        original = {key: np.zeros(shape)}
        metadata = dict(kernel=kernel, required=[key], integer_fields=[key])
        values = [holdout.make_case(original, metadata, c)[key] for c in holdout.cases()]
        assert len({v.tobytes() for v in values}) == 20
        assert all(np.array_equal(v, v.astype(int)) and np.all(v >= 0) for v in values)
        if key == "seq":
            assert all(np.all(v < 4) for v in values)


def test_probability_cases_stay_normalized_and_distinct():
    joint = np.full((8, 8), 0.5 / 64) + np.eye(8) * 0.5 / 8
    original = {"joint": joint}
    metadata = dict(kernel="mutual-information", required=["joint"])
    values = [holdout.make_case(original, metadata, c)["joint"] for c in holdout.cases()]
    assert len({v.tobytes() for v in values}) == 20
    assert all(np.all(v > 0) and np.isclose(v.sum(), 1) for v in values)


def test_forced_sparse_changes_preserve_dependent_initial_state():
    original = dict(r=np.ones(4), p=np.ones(4), rr=np.asarray(4.0))
    metadata = dict(kernel="poisson-cg", required=["r"])
    for case in holdout.cases():
        arrays = holdout.make_case(original, metadata, case)
        assert np.array_equal(arrays["p"], arrays["r"])
        assert arrays["rr"] == np.sum(arrays["r"] ** 2)


def test_variadic_interface_gets_independent_supplied_arrays():
    class Model(torch.nn.Module):
        def forward(self, *inputs):
            return inputs[0] @ inputs[1] @ inputs[2] @ inputs[3]

    original = {k: np.ones((3, 3)) * i for i, k in enumerate("ABCD", 1)}
    module = SimpleNamespace(
        make_model=Model,
        build_inputs=lambda **kwargs: tuple(
            torch.zeros(3, 3, dtype=torch.float64) for _ in range(4)
        ),
    )
    _, factory, _ = holdout.bind_inputs(module, original, "polybench-3mm", "mini")
    supplied = factory(original)
    assert all(
        np.array_equal(t.numpy(), original[k]) for t, k in zip(supplied, "ABCD", strict=True)
    )
    supplied[0].zero_()
    assert np.all(original["A"] == 1)
