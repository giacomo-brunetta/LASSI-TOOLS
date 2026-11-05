import operator

import torch
from torch import fx

from lassi_x import herbie
from lassi_x.herbie_fx import capture_with_leaf_methods, discover, promote_matmul, reinsert


class Cancellation(torch.nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        a = torch.sqrt(x + 1)
        b = torch.sqrt(x)
        return a - b


def test_cross_assignment_repair_and_fallback() -> None:
    model = fx.symbolic_trace(Cancellation())
    region = discover(model)[-1]
    assert "sqrt" in region.source and len(region.boundaries) == 1
    improved = "(FPCore (arg0) :precision binary32 (/ 1 (+ (sqrt (+ arg0 1)) (sqrt arg0))))"
    proposal = reinsert(model, region, improved)
    x = torch.tensor([1e8], dtype=torch.float32)
    assert model(x).item() == 0
    assert proposal(x).item() > 0
    assert torch.equal(proposal(x.double()), model(x.double()))
    assert discover(model) == discover(model)


class Opaque(torch.nn.Module):
    def forward(self, a: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        y = torch.matmul(a, x)
        z = torch.sqrt(y + 1)
        return z - torch.sqrt(y)


def test_opaque_boundary_roundtrip() -> None:
    model = fx.symbolic_trace(Opaque())
    region = discover(model)[-1]
    assert region.boundaries == ("matmul",)
    proposal = reinsert(model, region, herbie.fpcore(region.program(), {"v0": (1, 100)}))
    assert sum(n.target is torch.matmul for n in proposal.graph.nodes) == 1
    args = (torch.eye(3), torch.arange(1, 4, dtype=torch.float32))
    assert torch.equal(model(*args), proposal(*args))


def test_mutation_is_a_barrier() -> None:
    graph = fx.Graph()
    x = graph.placeholder("x")
    a = graph.call_function(torch.sqrt, (x,))
    graph.call_method("add_", (x, 1))
    result = graph.call_function(operator.sub, (a, x))
    graph.output(result)
    model = fx.GraphModule({}, graph)
    assert discover(model)[-1].boundaries == ("sqrt", "x")


def test_matmul_precision_proposal() -> None:
    model = fx.symbolic_trace(Opaque())
    proposal = promote_matmul(model, "matmul")
    for dtype in (torch.float16, torch.float64):
        a = torch.eye(3, dtype=dtype)
        x = torch.arange(1, 4, dtype=dtype)
        assert proposal(a, x).dtype == dtype
        assert torch.equal(proposal(a, x), model(a, x))


class WithScan(torch.nn.Module):
    def scan(self, x: torch.Tensor) -> torch.Tensor:
        if x.shape[0] % 2:
            return x + 1
        return x * 2

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.sqrt(self.scan(x)) + 1


def test_leaf_method_capture() -> None:
    model = WithScan()
    graph = capture_with_leaf_methods(model, ("scan",))
    assert type(model) is WithScan
    assert len([n for n in graph.graph.nodes if n.op == "call_module"]) == 1
    for size in (3, 4):
        x = torch.arange(size, dtype=torch.float64)
        assert torch.equal(graph(x), model(x))
    assert discover(graph, "binary64")
