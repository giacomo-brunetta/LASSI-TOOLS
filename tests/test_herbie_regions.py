import pytest
import torch

from lassi_x.herbie import fpcore
from lassi_x.herbie_regions import discover, reinsert

SOURCE = """import torch
from torch import nn
class Model(nn.Module):
    def forward(self, a, x, b):
        y = torch.matmul(a, x)
        z = y + b
        return (z.reshape(-1),)
"""


def test_region_roundtrip() -> None:
    regions = discover(SOURCE, "Model")
    assert len(regions) == 1
    program = regions[0].program()
    rewritten = reinsert(
        SOURCE, regions[0], fpcore(program, {a: (-2, 2) for a in program.arguments})
    )
    assert rewritten == reinsert(
        SOURCE, regions[0], fpcore(program, {a: (-2, 2) for a in program.arguments})
    )
    original_ns: dict[str, object] = {}
    new_ns: dict[str, object] = {}
    exec(SOURCE, original_ns)
    exec(rewritten, new_ns)
    for dtype in (torch.float32, torch.float64):
        args = (torch.eye(3, dtype=dtype), torch.arange(3, dtype=dtype), torch.ones(3, dtype=dtype))
        original = original_ns["Model"]
        new = new_ns["Model"]
        assert isinstance(original, type) and isinstance(new, type)
        assert torch.equal(original()(*args)[0], new()(*args)[0])
    with pytest.raises(ValueError, match="hash"):
        reinsert(SOURCE + "\n", regions[0], "")


def test_opaque_only_has_no_regions() -> None:
    assert discover(SOURCE.replace("y + b", "torch.matmul(a, x)"), "Model") == []
