from typing import Any

import pytest
import torch

from lassi_x.precision import compensated_sum
from lassi_x.precision_audit_worker import AuditedModel, audit_forward


def test_explicit_mixed_accumulation_is_labeled_and_requires_allowlist() -> None:
    class Reduction(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x.sum(dtype=torch.float32).to(x.dtype)

    report: dict[str, Any] = {
        "forward_calls": 0,
        "operations": 0,
        "violations": [],
        "arithmetic_policy": "mixed",
        "allowed_mixed_accumulation_ops": ["aten.sum.default"],
    }
    model = AuditedModel(Reduction(), torch.float16, report)
    model(torch.ones(4, dtype=torch.float16))
    assert report["arithmetic_class"] == "mixed_accumulation"
    assert report["wider_operations"][0]["operation"] == "aten.sum.default"
    assert report["observed_tensor_dtypes"] == ["torch.float16", "torch.float32"]
    report["allowed_mixed_accumulation_ops"] = []
    with pytest.raises(RuntimeError, match="precision policy"):
        model(torch.ones(4, dtype=torch.float16))


def test_mixed_track_still_rejects_whole_compute_and_wide_residual_state() -> None:
    class Promoted(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return (x.float() + x.float()).to(x.dtype)

    class WideState(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return (x.sum(dtype=torch.float32) + 1).to(x.dtype)

    for candidate in (Promoted(), WideState()):
        report: dict[str, Any] = {
            "forward_calls": 0,
            "operations": 0,
            "violations": [],
            "arithmetic_policy": "mixed",
            "allowed_mixed_accumulation_ops": ["aten.sum.default"],
        }
        with pytest.raises(RuntimeError, match="precision policy"):
            AuditedModel(candidate, torch.float16, report)(torch.ones(4, dtype=torch.float16))
        assert report["arithmetic_class"] == "wider_compute"


def test_target_arithmetic_passes() -> None:
    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return (x + x) / 2

    assert audit_forward(Model(), (torch.ones(4, dtype=torch.float16),), torch.float16)["passed"]


def test_hidden_promotion_rejected_even_if_output_casts_back() -> None:
    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return (x.float() * 2).to(x.dtype)

    report = audit_forward(Model(), (torch.ones(4, dtype=torch.bfloat16),), torch.bfloat16)
    assert not report["passed"]
    assert any("float32" in v for v in report["violations"])


def test_wide_reduction_and_host_scalar_rejected() -> None:
    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x + x.sum(dtype=torch.float32).item()

    assert not audit_forward(Model(), (torch.ones(4, dtype=torch.float16),), torch.float16)[
        "passed"
    ]


def test_integer_indexing_allowed() -> None:
    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x[torch.arange(x.numel())]

    assert audit_forward(Model(), (torch.ones(4, dtype=torch.float16),), torch.float16)["passed"]


def test_wide_stored_constants_cast_before_use_allowed() -> None:
    class Model(torch.nn.Module):
        constant: torch.Tensor

        def __init__(self) -> None:
            super().__init__()
            self.register_buffer("constant", torch.ones(4, dtype=torch.float64))
            self.register_buffer("unused", torch.ones(1, dtype=torch.float32))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x * self.constant.to(x)

    for dtype in (torch.float16, torch.bfloat16):
        assert audit_forward(Model(), (torch.ones(4, dtype=dtype),), dtype)["passed"]


def test_wide_constant_arithmetic_before_downcast_rejected() -> None:
    class Model(torch.nn.Module):
        constant: torch.Tensor

        def __init__(self) -> None:
            super().__init__()
            self.register_buffer("constant", torch.ones(4, dtype=torch.float64))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x * (self.constant * 2).to(x)

    assert not audit_forward(Model(), (torch.ones(4, dtype=torch.float16),), torch.float16)[
        "passed"
    ]


def test_wide_buffer_returned_without_arithmetic_rejected() -> None:
    class Model(torch.nn.Module):
        constant: torch.Tensor

        def __init__(self) -> None:
            super().__init__()
            self.register_buffer("constant", torch.ones(4, dtype=torch.float64))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.constant

    assert not audit_forward(Model(), (torch.ones(4, dtype=torch.float16),), torch.float16)[
        "passed"
    ]


def test_actual_model_late_promotion_is_caught() -> None:
    class Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.calls = 0

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            self.calls += 1
            return x + x if self.calls == 1 else (x.float() + x.float()).to(x.dtype)

    report: dict[str, Any] = {"forward_calls": 0, "operations": 0, "violations": []}
    model = AuditedModel(Model(), torch.float16, report)
    x = torch.ones(4, dtype=torch.float16)
    model(x)
    with pytest.raises(RuntimeError, match="precision policy"):
        model(x)
    assert report["forward_calls"] == 2


def test_stored_scalar_is_normalized_without_changing_source() -> None:
    class Model(torch.nn.Module):
        scale: torch.Tensor

        def __init__(self) -> None:
            super().__init__()
            self.register_buffer("scale", torch.tensor(0.2, dtype=torch.float64))

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.scale * x

    report: dict[str, Any] = {"forward_calls": 0, "operations": 0, "violations": []}
    model = AuditedModel(Model(), torch.float16, report)
    assert model(torch.ones(4, dtype=torch.float16)).dtype == torch.float16
    assert not report["violations"]


def test_double_word_helper_has_no_wide_recombination() -> None:
    class Model(torch.nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return compensated_sum(x, method="double-word")

    for dtype in (torch.float16, torch.bfloat16):
        assert audit_forward(Model(), (torch.ones(8, dtype=dtype),), dtype)["passed"]
