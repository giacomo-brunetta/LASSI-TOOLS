"""Prompt-level precision contracts shared by generation and repair stages."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import RunConfig


TARGET_FORMAT_CONTRACT = """Target-format-only arithmetic contract (hard requirement):
The GPU is a test platform for a destination without explicit wider tensor arithmetic.
For FP16/BF16 execution, keep main operators, persistent working state, reductions,
compensation/residual state, and outputs in the requested target format. Do not use
.float(), .double(), wider dtype casts, autocast, FP32/FP64 work arrays, or wider
helper implementations in the low-precision execution path. Casting the answer back
does not make a wider computation compliant. A wider hardware accumulator is allowed
only when the destination contract explicitly permits it; GPU availability is not permission.
FP32/FP64 branches remain available solely for the separate reference/control evaluations.
Input initialization may construct the reference fixture at its documented source precision
before one target-storage cast; do not move kernel computation into build_inputs or cache
answers there. forward must consume the actual supplied input values: never regenerate the
deterministic fixture, substitute constants, or branch on validation dataset/input identity.
Use scaling, stable reformulation, centering, changed reduction structure, or target-format
compensated/multiword arithmetic. Inspect helper implementations for hidden promotion.
If no compliant repair works, report failure. Do not weaken the workload or error gates.
Report actual storage/operator/accumulator/state/output formats and all casts honestly.
"""

MIXED_FORMAT_CONTRACT = """Mixed-precision arithmetic contract:
Keep the main computation in the requested low precision. Selective wider accumulation or
residual correction is allowed by explicit backend capabilities, but promoting the entire
kernel to FP32/FP64 is a fallback baseline, not a numerical repair. Casting the result back
does not change this. forward must use its supplied values, never regenerate known fixtures.
Report every wider operation and compare accuracy and latency with the existing FP32 baseline.
"""


def precision_contract(config: RunConfig) -> str:
    """Return the configured contract; this is instruction, not a runtime dtype audit."""
    if config.compensation.arithmetic_policy == "target_format_only":
        return TARGET_FORMAT_CONTRACT
    return MIXED_FORMAT_CONTRACT
