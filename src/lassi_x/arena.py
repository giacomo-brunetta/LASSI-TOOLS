from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any, cast

from .hermes import HermesSession
from .types import Candidate, Diagnostic, Status
from .validation import OracleResult, validate_candidate

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig

PLANNER_SYSTEM = """You are the LASSI-X scientific translation planner.
You plan semantically faithful C/C++ to PyTorch translations. You never edit files.
Use the lassi-x-machine-info and lassi-x-translate-kernel Hermes skills when available.
Return only the requested JSON; do not wrap it in Markdown."""

CANDIDATE_SYSTEM = """You are a LASSI-X PyTorch translation engineer.
Use the lassi-x-translate-kernel skill for generation and lassi-x-repair-candidate
plus lassi-x-compare-outputs when correcting a failed validation gate. Work only on
the explicitly named target file. Preserve the original algorithm and initialization."""


def _source_context(config: RunConfig) -> str:
    paths = [config.kernel.reference, *config.kernel.context]
    blocks: list[str] = []
    for relative in paths:
        path = config.resolve_project_path(relative)
        text = path.read_text(errors="replace")
        if len(text) > 100_000:
            text = text[:100_000] + "\n/* truncated by LASSI-X */\n"
        blocks.append(f"===== {relative} =====\n{text}")
    return "\n\n".join(blocks)


def _parse_json(text: str) -> list[object] | dict[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return cast("list[object] | dict[str, object]", json.loads(stripped))
    except json.JSONDecodeError as original:
        decoder = json.JSONDecoder()
        values: list[list[object] | dict[str, object]] = []
        for match in re.finditer(r"[\[{]", stripped):
            try:
                value, _ = decoder.raw_decode(stripped, match.start())
            except json.JSONDecodeError:
                continue
            if isinstance(value, (list, dict)):
                values.append(value)
        lists = [value for value in values if isinstance(value, list)]
        if lists:
            return max(lists, key=len)
        if values:
            return values[0]
        raise original


async def plan_strategies(config: RunConfig, workspace: Path) -> tuple[list[str], dict[str, Any]]:
    prompt = f"""Create exactly three materially distinct PyTorch translation strategies.

Kernel: {config.kernel.name}
Task: {config.kernel.task}

The implementations will be generated concurrently by three different configured models.
Every strategy must preserve initialization, operation semantics, output ordering, and
the build_inputs(device, dtype) / make_model() module contract.

Return a JSON array containing exactly three objects:
[{{"name":"short name","plan":"complete self-contained implementation plan"}}, ...]

Source context:
{_source_context(config)}
"""
    async with HermesSession(
        config.models.planner,
        cwd=workspace,
        system_prompt=PLANNER_SYSTEM,
        toolsets=["skills"],
        role="planner",
    ) as session:
        turn = await session.send(prompt)
    (workspace / "planner-response.txt").write_text(turn.text)
    raw = _parse_json(turn.text)
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("Hermes planner must return exactly three strategy objects")
    strategies = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict) or not str(item.get("plan") or "").strip():
            raise ValueError(f"planner strategy {index} is malformed")
        strategies.append(f"{item.get('name', f'candidate {index}')}\n{item['plan']}")
    return strategies, {
        "text": turn.text,
        "usage": {
            "input_tokens": turn.usage.input_tokens,
            "output_tokens": turn.usage.output_tokens,
            "estimated_cost_usd": turn.usage.estimated_cost_usd,
        },
    }


def _generation_prompt(
    config: RunConfig,
    candidate_id: str,
    strategy: str,
    target: Path,
) -> str:
    fixture = (
        str(config.resolve_project_path(config.oracle.input_fixture))
        if config.oracle.input_fixture
        else "none; reproduce the reference initialization exactly"
    )
    return f"""Implement arena candidate {candidate_id}.

Target file: {target}
Reference file: {config.resolve_project_path(config.kernel.reference)}
Input fixture: {fixture}
Kernel task: {config.kernel.task}

Assigned strategy:
{strategy}

Mandatory contract:
- Write one complete Python module to the exact target file.
- Define build_inputs(device="cpu", dtype=torch.float64, fixture=None) returning a tuple.
- Define make_model() returning torch.nn.Module.
- forward(*inputs) returns a tensor or tuple of tensors in canonical reference order.
- At FP64, output must match the original C/C++ reference, not merely the PyTorch code.
- Define LASSI_PRECISION metadata with storage, operator, accumulator, and output fields.
- Do not write benchmark, CSV, MLIR, or unrelated files.
- Run python -m py_compile on the target before responding.

Return a short plain-text implementation summary after writing the file.
"""


def _repair_prompt(target: Path, diagnostic: str, round_number: int) -> str:
    return f"""Correction round {round_number}.

The target remains: {target}
The external validator rejected the current implementation:

{diagnostic}

Inspect and repair the existing target in place. Fix the underlying algorithm or contract
problem without weakening validation, changing tolerances, or fabricating reference output.
Run python -m py_compile before returning. Return a short repair summary.
"""


async def generate_candidate(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    index: int,
    strategy: str,
) -> Candidate:
    candidate_id = f"c{index}"
    workspace = run_dir / "candidates" / candidate_id
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / "candidate.py"
    model = config.models.candidates[index - 1]
    candidate = Candidate(
        candidate_id=candidate_id,
        model=model.model,
        provider=model.provider,
        strategy=strategy,
        module_path=target,
    )
    session = HermesSession(
        model,
        cwd=workspace,
        system_prompt=CANDIDATE_SYSTEM,
        toolsets=["skills", "file", "terminal"],
        role=candidate_id,
    )
    try:
        turn = await session.send(_generation_prompt(config, candidate_id, strategy, target))
        candidate.usage.add(turn.usage)
        for attempt in range(config.arena.correction_rounds + 1):
            validation_dir = run_dir / "diagnostics" / candidate_id / f"attempt-{attempt}"
            validation_dir.mkdir(parents=True, exist_ok=True)
            result = await validate_candidate(config, target, oracle, validation_dir)
            if result.ok:
                candidate.status = Status.OK
                break
            if result.diagnostic is None:
                raise RuntimeError("validator failed without a diagnostic")
            candidate.diagnostics.append(result.diagnostic)
            if attempt >= config.arena.correction_rounds:
                candidate.status = Status.REJECTED
                break
            candidate.correction_rounds += 1
            turn = await session.send(
                _repair_prompt(target, result.diagnostic.for_agent(), candidate.correction_rounds)
            )
            candidate.usage.add(turn.usage)
    except Exception as exc:
        candidate.status = Status.CRASHED
        candidate.diagnostics.append(
            Diagnostic(gate="agent", message=f"{type(exc).__name__}: {exc}")
        )
    finally:
        await session.close()
    return candidate


async def run_arena(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
) -> tuple[list[Candidate], dict[str, Any]]:
    strategies, planner_record = await plan_strategies(config, run_dir)
    candidates = await asyncio.gather(
        *(
            generate_candidate(config, oracle, run_dir, index + 1, strategy)
            for index, strategy in enumerate(strategies)
        )
    )
    return candidates, planner_record
