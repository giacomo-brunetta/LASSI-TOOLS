from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any, cast

from .hermes import HermesSession
from .types import Candidate, Diagnostic, Status, Usage
from .validation import OracleResult, validate_candidate

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig

PLANNER_SYSTEM = """Role: senior scientific-computing architect and numerical-methods reviewer.

Your job is to study an authoritative C/C++ scientific kernel and design the requested number of
different, implementation-ready strategies for translating it to PyTorch. Another engineer
must be able to implement each strategy without guessing what you intended.

Planning responsibilities:
- Treat the C/C++ program as the semantic authority. Account for array initialization,
  dimensions, loop bounds, index expressions, update dependencies, reduction order,
  boundary behavior, aliasing, and the order of live outputs.
- Separate mathematical equivalence from implementation equivalence. Call out cases where
  reassociation, broadcasting, in-place updates, or dtype conversion could change results.
- Make the strategies materially different in operator structure or dataflow, such as
  direct tensor operations, contraction notation, batching, or carefully composed modules.
  Renaming variables or making cosmetic syntax changes does not create a distinct strategy.
- Keep every strategy feasible under the supplied module contract and suitable for later
  FP16/BF16 measurement, while making FP64 semantic correctness the first priority.
- Identify the important correctness risks and the concrete checks an implementer should
  perform. Do not invent missing facts; state conservative assumptions in the plan.

Tool and scope rules:
- Consult the lassi-x-machine-info and lassi-x-translate-kernel skills when useful.
- You are an architect, not the implementer: do not create, edit, or delete files.
- Follow the requested JSON schema exactly. Return JSON only, with no Markdown fences,
  commentary, preamble, or trailing explanation."""

CANDIDATE_SYSTEM = """Role: senior scientific software engineer specializing in faithful
C/C++-to-PyTorch translation and numerical debugging.

You own one arena candidate from initial implementation through any correction rounds. The
original C/C++ source is the semantic authority; the assigned strategy guides implementation
structure but never overrides reference behavior.

Engineering responsibilities:
- Read the reference and supplied context before writing code. Trace initialization,
  dimensions, loop bounds, index expressions, data dependencies, update order, reductions,
  boundary conditions, and the canonical order of returned live outputs.
- Implement the assigned strategy as clear, self-contained PyTorch. Preserve semantics before
  optimizing, and avoid accidental broadcasting, unintended aliasing, and silent dtype changes.
- Obey the requested module interface and precision metadata exactly. FP64 must reproduce the
  original program; lower-precision optimization and compensation happen only after that gate.
- Work only on the explicitly named target file. Do not create benchmark results, reference
  outputs, generated datasets, MLIR, reports, or unrelated helper files.
- Compile-check the target before reporting completion. Describe what you implemented briefly
  and accurately; do not claim validation that you did not run.

Repair responsibilities:
- Treat validator diagnostics as evidence. Locate the earliest violated assumption and repair
  its root cause rather than patching the reported symptom.
- For syntax or runtime failures, restore the module contract first. For shape or numerical
  failures, re-check initialization, indexing, update order, output ordering, and conversions
  against the C/C++ source.
- Never weaken tolerances, bypass validation, read or embed oracle output, return constants, or
  add low-precision compensation to conceal an FP64 semantic error.

Use lassi-x-translate-kernel for initial generation. During corrections, use
lassi-x-repair-candidate and lassi-x-compare-outputs as appropriate. Use file and terminal
tools only as needed for the assigned target and its verification."""


def _source_context(config: RunConfig) -> str:
    """Load the reference kernel and supporting files for an agent prompt.

    Each configured path is resolved relative to the project root. Individual files
    are truncated to keep a single unexpectedly large source from overwhelming the
    model context.

    Args:
        config: Validated run configuration containing the reference and context paths.

    Returns:
        Labeled source blocks joined into one prompt-ready string.

    """
    paths = [config.kernel.reference, *config.kernel.context]
    blocks: list[str] = []
    for relative in paths:
        path = config.resolve_project_path(relative)
        text = path.read_text(errors="replace")
        if len(text) > 100_000:
            text = text[:100_000] + "\n/* truncated by the orchestration layer */\n"
        blocks.append(f"===== {relative} =====\n{text}")
    return "\n\n".join(blocks)


def _parse_json(text: str) -> list[object] | dict[str, object]:
    """Extract a JSON array or object from a model response.

    The parser first accepts a plain JSON response or a single fenced JSON block. If
    the response also contains model commentary, it scans for embedded JSON values and
    prefers the largest array because planner output is expected to be an array.

    Args:
        text: Raw text returned by a Hermes model turn.

    Returns:
        The decoded JSON array or object.

    Raises:
        json.JSONDecodeError: If the response contains no decodable JSON value.

    """
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


def _parse_strategies(text: str, expected_count: int) -> list[dict[str, object]]:
    """Parse one unambiguous, schema-valid strategy array.

    Unlike the generic recovery parser, this function does not guess by array size. A
    response containing multiple plausible strategy arrays is rejected so the planner can
    repair its output on the next turn.

    Args:
        text: Raw planner response.
        expected_count: Number of strategy objects required by the arena.

    Returns:
        The unique array whose length and object schema match the request.

    Raises:
        ValueError: If no matching array exists or more than one is present.

    """
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    decoder = json.JSONDecoder()
    decoded: list[object] = []
    try:
        decoded.append(decoder.decode(stripped))
    except json.JSONDecodeError:
        for match in re.finditer(r"[\[{]", stripped):
            try:
                value, _ = decoder.raw_decode(stripped, match.start())
            except json.JSONDecodeError:
                continue
            decoded.append(value)
    matches: list[list[dict[str, object]]] = []
    fingerprints: set[str] = set()
    for value in decoded:
        if not isinstance(value, list) or len(value) != expected_count:
            continue
        if not all(
            isinstance(item, dict)
            and str(item.get("name") or "").strip()
            and str(item.get("plan") or "").strip()
            for item in value
        ):
            continue
        fingerprint = json.dumps(value, sort_keys=True)
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        matches.append(cast("list[dict[str, object]]", value))
    if len(matches) != 1:
        raise ValueError(
            f"expected one unambiguous array of {expected_count} strategy objects; "
            f"found {len(matches)}"
        )
    return matches[0]


async def plan_strategies(config: RunConfig, workspace: Path) -> tuple[list[str], dict[str, Any]]:
    """Ask the planner model for the configured number of translation strategies.

    The raw planner response is saved before parsing so malformed model output remains
    available for diagnosis. Each accepted strategy is normalized into a name followed
    by a self-contained implementation plan.

    Args:
        config: Validated run configuration, including the planner model selection.
        workspace: Run directory used for the planner session and response artifact.

    Returns:
        A pair containing normalized strategy strings and the planner response
        record with token and estimated-cost metadata.

    Raises:
        ValueError: If all attempts contain malformed or ambiguous strategy arrays.

    """
    count = config.arena.candidates
    prompt = f"""Create exactly {count} materially distinct PyTorch translation strategies.

Kernel: {config.kernel.name}
Task: {config.kernel.task}

The implementations will be generated concurrently by {count} configured model sessions.
Every strategy must preserve initialization, operation semantics, output ordering, and
the build_inputs(device, dtype) / make_model() module contract.

Return a JSON array containing exactly {count} objects:
[{{"name":"short name","plan":"complete self-contained implementation plan"}}, ...]

Source context:
{_source_context(config)}
"""
    total_usage = Usage()
    attempts: list[dict[str, Any]] = []
    strategies: list[str] | None = None
    async with HermesSession(
        config.models.planner,
        cwd=workspace,
        system_prompt=PLANNER_SYSTEM,
        toolsets=["skills"],
        role="planner",
    ) as session:
        for attempt in range(config.arena.planner_format_retries + 1):
            request = (
                prompt
                if attempt == 0
                else (
                    f"Your previous response was not one unambiguous JSON array of exactly {count} "
                    "strategy objects with non-empty name and plan fields. Repair only the output "
                    "shape. Return the complete JSON array and nothing else."
                )
            )
            turn = await session.send(request)
            total_usage.add(turn.usage)
            outcome = {
                "attempt": attempt,
                "text": turn.text,
                "completed": turn.completed,
                "exit_reason": turn.exit_reason,
                "agent_attempts": turn.attempts,
            }
            try:
                raw = _parse_strategies(turn.text, count)
            except ValueError as exc:
                outcome["parse_error"] = str(exc)
                attempts.append(outcome)
                continue
            attempts.append(outcome)
            strategies = [
                f"{item.get('name', f'candidate {index}')}\n{item['plan']}"
                for index, item in enumerate(raw, 1)
            ]
            break
    (workspace / "planner-responses.json").write_text(json.dumps(attempts, indent=2) + "\n")
    if strategies is None:
        raise ValueError(
            f"Hermes planner did not return {count} valid strategies after {len(attempts)} attempts"
        )
    return strategies, {
        "text": attempts[-1]["text"],
        "attempts": attempts,
        "usage": {
            "input_tokens": total_usage.input_tokens,
            "output_tokens": total_usage.output_tokens,
            "estimated_cost_usd": total_usage.estimated_cost_usd,
        },
    }


def _generation_prompt(
    config: RunConfig,
    candidate_id: str,
    strategy: str,
    target: Path,
) -> str:
    """Build the implementation request for one arena candidate.

    Args:
        config: Validated run configuration defining the kernel and oracle fixture.
        candidate_id: Stable identifier assigned to the candidate.
        strategy: Planner-produced name and implementation plan for this candidate.
        target: Exact Python module path the agent is allowed to write.

    Returns:
        A complete candidate-generation prompt containing paths, strategy, and module
        contract requirements.

    """
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
    """Build a diagnosis-driven correction request for a rejected candidate.

    Args:
        target: Existing candidate module that must be repaired in place.
        diagnostic: External validator evidence describing the failed gate.
        round_number: One-based correction round included in the agent context.

    Returns:
        A repair prompt that preserves validation policy and constrains file scope.

    """
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
    """Generate, validate, and optionally repair one arena candidate.

    One Hermes session owns the candidate across its initial implementation and all
    correction rounds. Validation is performed externally after every turn. Agent or
    validator exceptions are recorded on the candidate instead of escaping and
    cancelling the other concurrently generated candidates.

    Args:
        config: Validated run configuration and correction policy.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory for the current pipeline run.
        index: One-based candidate position used to select its configured model.
        strategy: Planner-produced strategy assigned to this candidate.

    Returns:
        The candidate record with final status, diagnostics, usage, and correction count.

    """
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
        candidate.turn_outcomes.append(
            {
                "completed": turn.completed,
                "exit_reason": turn.exit_reason,
                "attempts": turn.attempts,
            }
        )
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
            candidate.turn_outcomes.append(
                {
                    "completed": turn.completed,
                    "exit_reason": turn.exit_reason,
                    "attempts": turn.attempts,
                }
            )
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
    """Plan and execute the configured multi-candidate translation arena.

    Planning completes first so each candidate receives a distinct strategy. Candidate
    sessions then run concurrently, while each session independently performs its own
    sequential validation and correction loop.

    Args:
        config: Validated run configuration for planning and candidate generation.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory shared by planner and candidate workspaces.

    Returns:
        Completed candidate records and the auditable planner response record.

    Raises:
        json.JSONDecodeError: If the planner does not return decodable JSON.
        ValueError: If the planner does not return exactly three valid strategies.

    """
    strategies, planner_record = await plan_strategies(config, run_dir)
    candidates = await asyncio.gather(
        *(
            generate_candidate(config, oracle, run_dir, index + 1, strategy)
            for index, strategy in enumerate(strategies)
        )
    )
    return candidates, planner_record
