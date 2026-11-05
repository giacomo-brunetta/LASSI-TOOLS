"""Frozen, no-model Stage 2 proposal replay and validation for Torch FX.

Herbie search is an upstream preparation action. This step consumes immutable
FPCore results and explicit matmul choices; it never samples or searches.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Literal, Protocol

if TYPE_CHECKING:
    from torch import fx

from lassi_x import herbie, herbie_fx


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class Proposal:
    id: str
    kind: Literal["herbie", "matmul_fp32"]
    root: str
    fpcore: str = ""
    # Domains are explicit bounds on region boundary values, not model inputs.
    domains: tuple[tuple[str, float, float], ...] = ()


def implementation_identity() -> str:
    return _sha(
        Path(herbie.__file__).read_text()
        + Path(herbie_fx.__file__).read_text()
        + Path(__file__).read_text()
    )


@dataclass(frozen=True)
class Plan:
    source_sha256: str
    graph_sha256: str
    contract_sha256: str
    environment_sha256: str
    precision: Literal["binary16", "bfloat16", "binary32", "binary64"]
    proposals: tuple[Proposal, ...]
    maximum: int = 8
    schema: int = 1
    implementation_sha256: str = field(default_factory=implementation_identity)


@dataclass(frozen=True)
class Validation:
    """Validator owns reference/input parity and executed precision evidence."""

    fp64_pass: bool
    fp32_pass: bool
    target_pass: bool
    precision_pass: bool
    error: float
    evidence_sha256: str

    def __post_init__(self) -> None:
        if any(
            type(x) is not bool
            for x in (self.fp64_pass, self.fp32_pass, self.target_pass, self.precision_pass)
        ):
            raise ValueError("Validation gates must be booleans")
        if not math.isfinite(self.error) or self.error < 0:
            raise ValueError("Error must be finite and nonnegative")
        _digest(self.evidence_sha256)

    @property
    def passes(self) -> bool:
        return self.fp64_pass and self.fp32_pass and self.target_pass and self.precision_pass


class Validator(Protocol):
    def __call__(self, graph: fx.GraphModule, precision: str, proposal_id: str, /) -> Validation:
        """Run the frozen, bounded reference suite and precision audit; no model calls."""


def _digest(value: str) -> None:
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("Require a SHA256 hex identity")


def run(
    graph: fx.GraphModule,
    plan: Plan,
    *,
    source: str,
    contract: bytes,
    environment: bytes,
    output: Path,
    validate: Validator,
) -> fx.GraphModule | None:
    """Replay all declared independent proposals; return the best accepted graph.

    The supplied graph must be captured from the declared source in the frozen
    environment. Model state, leaf implementations and workload identities must
    be included in the caller's contract/environment; graph code alone is not a
    complete model fingerprint. Validator deadlines are owned by its executor.
    """
    for identity in (
        plan.source_sha256,
        plan.graph_sha256,
        plan.contract_sha256,
        plan.environment_sha256,
    ):
        _digest(identity)
    if (
        plan.implementation_sha256 != implementation_identity()
        or plan.schema != 1
        or plan.precision not in herbie.PRECISIONS
        or plan.maximum < 0
        or len(plan.proposals) > plan.maximum
        or len({p.id for p in plan.proposals}) != len(plan.proposals)
        or any(not p.id or p.id == "baseline" for p in plan.proposals)
    ):
        raise ValueError("Invalid frozen plan or budget")
    if (
        plan.source_sha256 != _sha(source)
        or plan.graph_sha256 != _sha(graph.code)
        or plan.contract_sha256 != hashlib.sha256(contract).hexdigest()
        or plan.environment_sha256 != hashlib.sha256(environment).hexdigest()
    ):
        raise ValueError("Frozen input identity mismatch")
    output.mkdir(parents=True, exist_ok=False)
    plan_text = json.dumps(asdict(plan), sort_keys=True, indent=2)
    (output / "plan.json").write_text(plan_text + "\n")
    (output / "source.py").write_text(source)
    (output / "graph.py").write_text(graph.code)
    (output / "contract.json").write_bytes(contract)
    (output / "environment.json").write_bytes(environment)
    records: list[dict[str, object]] = []
    selected: str | None = None

    def save(status: str) -> None:
        report = {
            "schema": 1,
            "status": status,
            "plan_sha256": _sha(plan_text),
            "selected": selected,
            "records": records,
            "model_calls": 0,
            "herbie_searches": 0,
            "adapter_sha256": _sha(Path(__file__).read_text()),
        }
        temporary = output / "result.tmp"
        temporary.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
        temporary.replace(output / "result.json")

    save("running")
    try:
        baseline = validate(copy.deepcopy(graph), plan.precision, "baseline")
    except Exception as exc:
        records.append({"id": "baseline", "status": "incomplete", "reason": str(exc)})
        save("blocked")
        return None
    records.append({"id": "baseline", "validation": asdict(baseline)})
    if not baseline.fp64_pass or (
        plan.precision in ("binary16", "bfloat16") and not baseline.fp32_pass
    ):
        save("blocked")
        return None
    regions = {r.root: r for r in herbie_fx.discover(graph, plan.precision)}
    best: fx.GraphModule | None = None
    best_error = baseline.error
    for index, proposal in enumerate(plan.proposals):
        record: dict[str, object] = {
            "id": proposal.id,
            "kind": proposal.kind,
            "root": proposal.root,
            "status": "running",
        }
        records.append(record)
        save("running")
        try:
            if proposal.kind == "herbie":
                if re.search(
                    r"(?m)^;;\s+(?:(?:Crash|Error) in\b|.* times out in\b)", proposal.fpcore
                ):
                    raise ValueError("Herbie result reports failure")
                region = regions[proposal.root]
                domains = {name: (lo, hi) for name, lo, hi in proposal.domains}
                if len(domains) != len(proposal.domains):
                    raise ValueError("Duplicate domains")
                original = herbie.parse(herbie.fpcore(region.program(), domains))[0]
                improved = herbie.parse(proposal.fpcore)
                if (
                    len(improved) != 1
                    or not isinstance(original, list)
                    or not isinstance(improved[0], list)
                ):
                    raise ValueError("Require one FPCore result")
                args = [f"arg{i}" for i in range(len(region.program().arguments))]
                if herbie._bounds(
                    herbie._properties(original[2:-1]).get(":pre"), args
                ) != herbie._bounds(herbie._properties(improved[0][2:-1]).get(":pre"), args):
                    raise ValueError("Herbie changed input domains")
                candidate = herbie_fx.reinsert(graph, region, proposal.fpcore)
            elif proposal.kind == "matmul_fp32":
                if (
                    plan.precision not in ("binary16", "bfloat16")
                    or proposal.fpcore
                    or proposal.domains
                ):
                    raise ValueError("Invalid matmul promotion contract")
                candidate = herbie_fx.promote_matmul(graph, proposal.root)
            else:
                raise ValueError("Unknown proposal kind")
            (output / f"proposal-{index:04d}.py").write_text(candidate.code)
            result = validate(copy.deepcopy(candidate), plan.precision, proposal.id)
            accepted = result.passes and result.error < baseline.error
            record.update(
                status="accepted" if accepted else "rejected",
                validation=asdict(result),
                graph_sha256=_sha(candidate.code),
            )
            if accepted and result.error < best_error:
                selected, best, best_error = proposal.id, candidate, result.error
        except Exception as exc:
            record.update(status="incomplete", reason=f"{type(exc).__name__}: {exc}")
        save("running")
    save("complete")
    return best
