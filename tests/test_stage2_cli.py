import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest
import torch
from torch import fx

from lassi_x.stage2_cli import execute
from lassi_x.stage2_deterministic import Plan


class Identity(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x


def test_replay_entrypoint(tmp_path: Path) -> None:
    source = "frozen source"
    driver = """import torch
from torch import fx
from lassi_x.stage2_deterministic import Validation
class Identity(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x
def build_graph(source, contract):
    return fx.symbolic_trace(Identity())
def validate(graph, precision, proposal_id):
    return Validation(True, True, True, True, 0, 'a' * 64)
"""

    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    plan = Plan(
        sha(source.encode()),
        sha(fx.symbolic_trace(Identity()).code.encode()),
        sha(b"{}"),
        sha(b"{}"),
        "binary32",
        (),
    )
    for name, value in {
        "source.py": source,
        "driver.py": driver,
        "contract.json": "{}",
        "environment.json": "{}",
        "plan.json": json.dumps(asdict(plan)),
    }.items():
        (tmp_path / name).write_text(value)
    config = {
        "schema": 1,
        "source": "source.py",
        "plan": "plan.json",
        "contract": "contract.json",
        "environment": "environment.json",
        "driver": "driver.py",
        "driver_sha256": sha(driver.encode()),
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    assert execute(path, tmp_path / "output") == 1
    assert json.loads((tmp_path / "output/result.json").read_text())["status"] == "complete"
    with pytest.raises(FileExistsError):
        execute(path, tmp_path / "output")
    (tmp_path / "driver.py").write_text('raise AssertionError("must not execute")')
    with pytest.raises(ValueError, match="identity mismatch"):
        execute(path, tmp_path / "rejected")
    assert not (tmp_path / "rejected").exists()
