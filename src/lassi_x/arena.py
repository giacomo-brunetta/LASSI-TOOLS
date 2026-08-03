from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any, cast

from .hermes import HermesSession
from .types import Candidate, Diagnostic, Status
from .validation import OracleResult, fixture_relative_path, validate_candidate

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig
    from .execution import ExecutionContext

PLANNER_SYSTEM = """Role: senior scientific-computing architect and numerical-methods reviewer.

Your job is to study an authoritative C/C++ scientific kernel and design three genuinely
different, implementation-ready strategies for translating it to PyTorch. Another engineer
must be able to implement each strategy without guessing what you intended.

Planning responsibilities:
- Treat the C/C++ program as the semantic authority. Account for array initialization,
  dimensions, loop bounds, index expressions, update dependencies, reduction order,
  boundary behavior, aliasing, and the order of live outputs.
- Separate mathematical equivalence from implementation equivalence. Call out cases where
  reassociation, broadcasting, in-place updates, or dtype conversion could change results.
- Make the three strategies materially different in operator structure or dataflow, such as
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
lassi-x-repair-candidate and lassi-x-compare-outputs as appropriate.

Workspace access:
- Your only access to files and commands is the assigned workspace toolset (list_resources,
  run_command, write_file, read_file, list_files). All paths are workspace-relative.
- Call list_resources first when choosing where to run commands; pass the chosen resource
  name to later calls, or omit it to use the default machine."""


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


async def plan_strategies(config: RunConfig, workspace: Path) -> tuple[list[str], dict[str, Any]]:
    """Ask the planner model for exactly three translation strategies.

    The raw planner response is saved before parsing so malformed model output remains
    available for diagnosis. Each accepted strategy is normalized into a name followed
    by a self-contained implementation plan.

    Args:
        config: Validated run configuration, including the planner model selection.
        workspace: Run directory used for the planner session and response artifact.

    Returns:
        A pair containing three normalized strategy strings and the planner response
        record with token and estimated-cost metadata.

    Raises:
        json.JSONDecodeError: If the planner response contains no valid JSON.
        ValueError: If the response is not exactly three well-formed strategy objects.

    """
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


async def _stage_reference(
    config: RunConfig, execution: ExecutionContext, workspace: str
) -> list[str]:
    """Stage the reference kernel, context files, and fixture into a workspace.

    With workspace-confined tools the agent cannot read project paths, so the
    authoritative sources are staged under ``reference/`` inside the workspace
    on every resource before the session starts.

    Args:
        config: Validated run configuration naming the reference and context files.
        execution: Running execution context serving the workspace.
        workspace: Workspace identifier.

    Returns:
        Workspace-relative paths of the staged source files.

    """
    staged = []
    for relative in [config.kernel.reference, *config.kernel.context]:
        source = config.resolve_project_path(relative)
        destination = f"reference/{source.name}"
        await execution.stage_bytes(workspace, destination, source.read_bytes())
        staged.append(destination)
    fixture = fixture_relative_path(config)
    if fixture is not None and config.oracle.input_fixture is not None:
        source = config.resolve_project_path(config.oracle.input_fixture)
        await execution.stage_bytes(workspace, fixture, source.read_bytes())
    return staged


def _generation_prompt(
    config: RunConfig,
    candidate_id: str,
    strategy: str,
    toolset: str,
    staged_reference: list[str],
) -> str:
    """Build the implementation request for one arena candidate.

    Args:
        config: Validated run configuration defining the kernel and oracle fixture.
        candidate_id: Stable identifier assigned to the candidate.
        strategy: Planner-produced name and implementation plan for this candidate.
        toolset: Name of the workspace toolset assigned to this candidate.
        staged_reference: Workspace-relative paths of the staged reference sources.

    Returns:
        A complete candidate-generation prompt containing paths, strategy, and module
        contract requirements.

    """
    fixture = (
        fixture_relative_path(config) or "none; reproduce the reference initialization exactly"
    )
    reference_lines = "\n".join(f"- {path}" for path in staged_reference)
    return f"""Implement arena candidate {candidate_id}.

Workspace toolset: {toolset} (all paths below are workspace-relative)
Target file: candidate.py
Reference sources staged in your workspace:
{reference_lines}
Input fixture: {fixture}
Kernel task: {config.kernel.task}

Assigned strategy:
{strategy}

Mandatory contract:
- Write one complete Python module to candidate.py using write_file.
- Write candidate.py on the default machine (omit the resource argument for write_file);
  other machines are for exploration and scratch commands only.
- Define build_inputs(device="cpu", dtype=torch.float64, fixture=None) returning a tuple.
- Define make_model() returning torch.nn.Module.
- forward(*inputs) returns a tensor or tuple of tensors in canonical reference order.
- At FP64, output must match the original C/C++ reference, not merely the PyTorch code.
- Do not write benchmark, CSV, MLIR, or unrelated files.
- Define LASSI_PRECISION metadata with storage, operator, accumulator, and output fields.
- Compile-check with run_command: python -m py_compile candidate.py before responding.

Return a short plain-text implementation summary after writing the file.
"""


def _repair_prompt(diagnostic: str, round_number: int) -> str:
    """Build a diagnosis-driven correction request for a rejected candidate.

    Args:
        diagnostic: External validator evidence describing the failed gate.
        round_number: One-based correction round included in the agent context.

    Returns:
        A repair prompt that preserves validation policy and constrains file scope.

    """
    return f"""Correction round {round_number}.

The target remains candidate.py in your workspace.
The external validator rejected the current implementation:

{diagnostic}

Inspect and repair the existing target in place. Fix the underlying algorithm or contract
problem without weakening validation, changing tolerances, or fabricating reference output.
Compile-check with run_command: python -m py_compile candidate.py before returning.
Return a short repair summary.
"""


async def generate_candidate(
    config: RunConfig,
    oracle: OracleResult,
    run_dir: Path,
    execution: ExecutionContext,
    index: int,
    strategy: str,
) -> Candidate:
    """Generate, validate, and optionally repair one arena candidate.

    One Hermes session owns the candidate across its initial implementation and all
    correction rounds. The session's only filesystem and command access is its
    header-pinned workspace toolset served by the run's MCP server, so every tool
    call executes on the configured resources. Validation is performed externally
    after every turn. Agent or validator exceptions are recorded on the candidate
    instead of escaping and cancelling the other concurrently generated candidates.

    Args:
        config: Validated run configuration and correction policy.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory for the current pipeline run.
        execution: Running execution context serving workspace tool calls.
        index: One-based candidate position used to select its configured model.
        strategy: Planner-produced strategy assigned to this candidate.

    Returns:
        The candidate record with final status, diagnostics, usage, and correction count.

    """
    candidate_id = f"c{index}"
    mirror = execution.workspace_dir(candidate_id)
    mirror.mkdir(parents=True, exist_ok=True)
    staged_reference = await _stage_reference(config, execution, candidate_id)
    toolset = execution.register_workspace(candidate_id)
    model = config.models.candidates[index - 1]
    candidate = Candidate(
        candidate_id=candidate_id,
        model=model.model,
        provider=model.provider,
        strategy=strategy,
        module_path=mirror / "candidate.py",
    )
    session = HermesSession(
        model,
        cwd=mirror,
        system_prompt=CANDIDATE_SYSTEM,
        toolsets=["skills", toolset],
        role=candidate_id,
    )
    try:
        turn = await session.send(
            _generation_prompt(config, candidate_id, strategy, toolset, staged_reference)
        )
        candidate.usage.add(turn.usage)
        backend = execution.backend()
        for attempt in range(config.arena.correction_rounds + 1):
            validation_dir = run_dir / "diagnostics" / candidate_id / f"attempt-{attempt}"
            validation_dir.mkdir(parents=True, exist_ok=True)
            result = await validate_candidate(config, backend, candidate_id, oracle, validation_dir)
            if result.ok:
                candidate.status = Status.OK
                await execution.mirror_file(candidate_id, "candidate.py")
                break
            if result.diagnostic is None:
                raise RuntimeError("validator failed without a diagnostic")
            candidate.diagnostics.append(result.diagnostic)
            if attempt >= config.arena.correction_rounds:
                candidate.status = Status.REJECTED
                break
            candidate.correction_rounds += 1
            turn = await session.send(
                _repair_prompt(result.diagnostic.for_agent(), candidate.correction_rounds)
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
    execution: ExecutionContext,
) -> tuple[list[Candidate], dict[str, Any]]:
    """Plan and execute the three-candidate translation arena.

    Planning completes first so each candidate receives a distinct strategy. Candidate
    sessions then run concurrently, while each session independently performs its own
    sequential validation and correction loop.

    Args:
        config: Validated run configuration for planning and candidate generation.
        oracle: Authoritative output produced from the original C/C++ reference.
        run_dir: Root artifact directory shared by planner and candidate workspaces.
        execution: Running execution context serving workspace tool calls.

    Returns:
        The three completed candidate records and the auditable planner response record.

    Raises:
        json.JSONDecodeError: If the planner does not return decodable JSON.
        ValueError: If the planner does not return exactly three valid strategies.

    """
    strategies, planner_record = await plan_strategies(config, run_dir)
    candidates = await asyncio.gather(
        *(
            generate_candidate(config, oracle, run_dir, execution, index + 1, strategy)
            for index, strategy in enumerate(strategies)
        )
    )
    return candidates, planner_record
