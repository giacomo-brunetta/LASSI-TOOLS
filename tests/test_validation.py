from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import yaml

from lassi_x.config import RunConfig
from lassi_x.execution import LocalExecutionBackend
from lassi_x.validation import (
    build_oracle,
    scrape_polybench_dump,
    validate_candidate,
    validate_fp32_collapse,
)

from .test_config import minimal_config

if TYPE_CHECKING:
    from pathlib import Path

C_REFERENCE = r"""
#include <stdio.h>
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "w");
    if (!f) return 2;
    fprintf(f, "1\n2\n3\n");
    fclose(f);
    return 0;
}
"""

GOOD_MODULE = """
import torch
from torch import nn
LASSI_PRECISION = {
    "storage": "requested", "operator": "requested",
    "accumulator": "requested", "output": "requested",
}
def build_inputs(device="cpu", dtype=torch.float64, fixture=None):
    return (torch.tensor([1., 2., 3.], device=device, dtype=dtype),)
class Model(nn.Module):
    def forward(self, x):
        return x
def make_model():
    return Model()
"""

BAD_MODULE = GOOD_MODULE.replace("return x\n", "return x + 1\n")


def _setup(tmp_path: Path) -> tuple[RunConfig, LocalExecutionBackend]:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    root = tmp_path / "workspaces"
    for workspace, module in (("good", GOOD_MODULE), ("bad", BAD_MODULE)):
        (root / workspace).mkdir(parents=True)
        (root / workspace / "candidate.py").write_text(module)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    return RunConfig.load(config_path), LocalExecutionBackend(root, "test")


def test_original_c_reference_is_authoritative(tmp_path: Path) -> None:
    config, backend = _setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    accepted = asyncio.run(
        validate_candidate(config, backend, "good", oracle, tmp_path / "good-artifacts")
    )
    rejected = asyncio.run(
        validate_candidate(config, backend, "bad", oracle, tmp_path / "bad-artifacts")
    )
    assert accepted.ok
    assert not rejected.ok
    assert rejected.diagnostic is not None
    assert rejected.diagnostic.gate == "equivalence"
    assert (tmp_path / "good-artifacts" / "fp64.npy").is_file()


def test_missing_module_reports_write_gate(tmp_path: Path) -> None:
    config, backend = _setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    result = asyncio.run(
        validate_candidate(config, backend, "good", oracle, tmp_path / "a", module_name="nope.py")
    )
    assert not result.ok
    assert result.diagnostic is not None
    assert result.diagnostic.gate == "write"


def test_fp32_self_consistency_does_not_replace_c_oracle(tmp_path: Path) -> None:
    config, backend = _setup(tmp_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    # A biased module agrees with itself at FP32.
    collapse = asyncio.run(
        validate_fp32_collapse(config, backend, "bad", "bad", tmp_path / "collapse")
    )
    authoritative = asyncio.run(
        validate_candidate(config, backend, "bad", oracle, tmp_path / "authoritative")
    )
    assert collapse.ok
    assert not authoritative.ok


def test_polybench_dump_parser_ignores_labels() -> None:
    values = scrape_polybench_dump(
        "noise\n==BEGIN DUMP_ARRAYS==\nbegin dump: G\n1.0 2.5\n"
        "end   dump: G\n==END   DUMP_ARRAYS==\n"
    )
    assert values.tolist() == [1.0, 2.5]
