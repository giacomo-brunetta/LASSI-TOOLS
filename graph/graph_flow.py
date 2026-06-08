from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from claude_agent_sdk import (
    AgentDefinition,
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
)
from pydantic_graph import GraphBuilder, StepContext, TypeExpression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lassi.core.compiler import Compiler, CompilerTool
from lassi.core.executer import FunctionalValidator, WrongOutput, WrongRetCode
from lassi.core.source_file import SourceFile


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "graph_code_test.json"
BUILD_ROOT = Path(".verify/refactoring")
LASSI_DIR = Path("LASSI")
CONTEXT_FILE = "00_context.md"
ANALYSIS_FILE = "01_analysis.md"
PLAN_FILE = "02_plan.md"
CHANGES_FILE = "03_changes.md"
CLAUDE_MODEL = "claude-opus-4-7"
CONFIG_BUILDER_AGENT = "config-builder"
ANALYST_AGENT = "analyst"
PLANNER_AGENT = "planner"
CODER_AGENT = "coder"

Ok = Literal["ok"]
Missing = Literal["missing"]
Fail = Literal["fail"]


CONFIG_BUILDER = AgentDefinition(
    description=(
        "Discover the compile command for a single C/C++ source in the repo and emit a "
        "pipeline config JSON, including golden outputs captured from the original binary."
    ),
    prompt=(
        "You produce a JSON pipeline config for a C/C++ optimization workflow.\n\n"
        "Inputs you will be given each turn:\n"
        "- repo_path: the working directory containing the source.\n"
        "- config_path: the file you must write the final JSON to.\n\n"
        "What to do:\n"
        "1. Explore the repo and identify the single source file that should be optimized "
        "(typically the only top-level .c / .cpp / .cu file with a main()).\n"
        "2. Pick a compiler in this order of preference: clang, clang++, gcc, g++. Verify it is "
        "actually installed by running `--version`.\n"
        "3. Discover compile flags that work with `<compiler> <flags> <source> -o <out>`:\n"
        "   - correctness flags: include `-O0` plus whatever else is needed for a clean build "
        "(e.g. `-lm`, `-std=c11`, warning flags). Keep it minimal.\n"
        "   - performance flags: same baseline but with `-O3` instead of `-O0`.\n"
        "   You may edit files in the repo to make the build clean, but only if necessary.\n"
        "4. Pick a name for the optimized variant (e.g. `optimized.c` next to the original).\n"
        "5. Choose 5-8 small CLI argument sets that exercise the program. For each, run the "
        "O3-built original binary and capture its exact stdout (verbatim, including trailing "
        "newlines) as the golden output.\n"
        "6. Pick one larger argument set suitable for benchmarking (the program should run for "
        "tens of milliseconds, not a microsecond and not minutes).\n"
        "7. Write the final JSON to `config_path` with this exact schema:\n"
        "{\n"
        "  \"sources\": { \"original\": \"<rel-path>\", \"optimized\": \"<rel-path>\" },\n"
        "  \"compiler\": \"clang|clang++|gcc|g++\",\n"
        "  \"flags\":   { \"correctness\": \"<str>\", \"performance\": \"<str>\" },\n"
        "  \"arguments\": {\n"
        "    \"benchmark\": \"<str>\",\n"
        "    \"benchmark_runs\": 5,\n"
        "    \"golden\": [ { \"args\": \"<str>\", \"stdout\": \"<str>\" }, ... ]\n"
        "  }\n"
        "}\n"
        "Paths must be relative to repo_path. Do NOT include any commentary, markdown, or "
        "code fences in the file - it must be valid JSON.\n\n"
        "8. Reply with a short one-paragraph summary of: the chosen compiler, the correctness "
        "and performance flag strings, and how many golden cases you captured."
    ),
    tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
    model="inherit",
)


@dataclass
class PipelineConfig:
    original_path: Path
    optimized_path: Path
    compiler: Compiler
    correctness_flags: str
    performance_flags: str
    benchmark_args: str
    benchmark_runs: int
    golden_outputs: list[tuple[str, str]]

    @classmethod
    def load(cls, path: Path) -> PipelineConfig:
        raw = json.loads(path.read_text())
        sources = raw["sources"]
        flags = raw["flags"]
        args = raw["arguments"]
        golden = [(case["args"], case["stdout"]) for case in args.get("golden", [])]
        return cls(
            original_path=Path(sources["original"]),
            optimized_path=Path(sources["optimized"]),
            compiler=Compiler.from_string(raw["compiler"]),
            correctness_flags=flags["correctness"],
            performance_flags=flags["performance"],
            benchmark_args=args["benchmark"],
            benchmark_runs=int(args.get("benchmark_runs", 5)),
            golden_outputs=golden,
        )


@dataclass
class RefactoringState:
    config_path: Path = field(default_factory=lambda: DEFAULT_CONFIG_PATH)
    repo_path: Path = field(default_factory=lambda: Path.cwd().resolve())
    config: PipelineConfig | None = None
    original: SourceFile | None = None
    optimized: SourceFile | None = None
    claude_client: ClaudeSDKClient | None = field(default=None, repr=False)
    claude_result: str | None = None
    instructions: list[Path] = field(default_factory=list)
    error: str | None = None


def _log_tool_use(block: ToolUseBlock) -> None:
    raw = block.input if isinstance(block.input, dict) else {}
    if block.name == "Task":
        sub = raw.get("subagent_type") or "<unspecified>"
        desc = raw.get("description") or raw.get("prompt", "")
        if isinstance(desc, str) and len(desc) > 120:
            desc = desc[:117] + "..."
        logger.info("claude dispatched agent '%s' (task: %s)", sub, desc)
    elif block.name == "Skill":
        skill = raw.get("skill") or raw.get("name") or "<unknown>"
        args = raw.get("args") or raw.get("arguments") or ""
        logger.info("claude invoked skill '%s' args=%r", skill, args)
    elif block.name == "Bash":
        cmd = raw.get("command", "")
        if len(cmd) > 200:
            cmd = cmd[:197] + "..."
        logger.info("claude ran bash: %s", cmd)
    else:
        logger.debug("claude tool use: %s input=%s", block.name, raw)


def _log_system_message(message: SystemMessage) -> None:
    subtype = getattr(message, "subtype", None) or "system"
    data = getattr(message, "data", {}) or {}
    if subtype == "init":
        logger.info(
            "claude session init: model=%s tools=%s agents=%s",
            data.get("model"),
            data.get("tools") or data.get("available_tools"),
            data.get("agents"),
        )
    else:
        logger.debug("claude system event %s: %s", subtype, data)


async def claude_send(client: ClaudeSDKClient, prompt: str) -> str:
    await client.query(prompt)
    final_text = ""
    async for message in client.receive_response():
        if isinstance(message, SystemMessage):
            _log_system_message(message)
        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    _log_tool_use(block)
                elif isinstance(block, TextBlock) and block.text:
                    final_text = block.text
        elif isinstance(message, ResultMessage):
            if message.result:
                final_text = message.result
            logger.info(
                "claude turn finished: stop_reason=%s duration_ms=%s cost=%s",
                getattr(message, "stop_reason", None),
                getattr(message, "duration_ms", None),
                getattr(message, "total_cost_usd", None),
            )
    return final_text


async def _ensure_claude_client(state: RefactoringState) -> ClaudeSDKClient:
    if state.claude_client is not None:
        return state.claude_client
    options = ClaudeAgentOptions(
        cwd=str(state.repo_path),
        model=CLAUDE_MODEL,
        permission_mode="bypassPermissions",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task"],
        agents={CONFIG_BUILDER_AGENT: CONFIG_BUILDER},
    )
    client = ClaudeSDKClient(options=options)
    await client.connect()
    state.claude_client = client
    return client


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the graph-based refactoring pipeline against a pipeline config.",
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=(
            "Path to the pipeline config JSON. If the file does not exist, an agent will "
            "be asked to generate it from the repo contents."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repo to operate on (default: current working directory).",
    )
    return parser.parse_args(argv)


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config_path = args.config_path.resolve()
    repo_path = (args.repo or Path.cwd()).resolve()

    g = GraphBuilder(state_type=RefactoringState, output_type=str)

    @g.step
    async def load_config(ctx: StepContext[RefactoringState, None, object]) -> Ok | Missing | Fail:
        cfg_path = ctx.state.config_path
        if not cfg_path.exists():
            logger.info("config %s not found; will ask agent to generate it", cfg_path)
            return "missing"
        try:
            ctx.state.config = PipelineConfig.load(cfg_path)
            logger.info(
                "loaded config from %s: compiler=%s sources=(%s -> %s) golden_cases=%d",
                cfg_path,
                ctx.state.config.compiler.value,
                ctx.state.config.original_path,
                ctx.state.config.optimized_path,
                len(ctx.state.config.golden_outputs),
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"failed to parse config {cfg_path}: {exc}"
            return "fail"

    @g.step
    async def generate_config(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        cfg_path = ctx.state.config_path
        repo = ctx.state.repo_path
        logger.info("asking agent to generate config at %s for repo %s", cfg_path, repo)
        try:
            client = await _ensure_claude_client(ctx.state)
            prompt = "\n".join([
                f"repo_path: {repo}",
                f"config_path: {cfg_path}",
                "",
                f"Dispatch the '{CONFIG_BUILDER_AGENT}' subagent via the Task tool with the "
                "two paths above and the instructions baked into its system prompt. After it "
                "finishes, verify the file exists and is valid JSON, then relay its summary.",
            ])
            ctx.state.claude_result = await claude_send(client, prompt)
            if not cfg_path.exists():
                raise FileNotFoundError(f"agent did not create {cfg_path}")
            # Sanity-parse so a malformed file fails here, not later.
            json.loads(cfg_path.read_text())
            return "ok"
        except Exception as exc:
            ctx.state.error = f"config generation failed: {exc}"
            return "fail"

    @g.step
    async def sanity_check_original(
        ctx: StepContext[RefactoringState, None, object],
    ) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info(
            "sanity-checking original (%s) against %d golden case(s)",
            cfg.original_path,
            len(cfg.golden_outputs),
        )
        try:
            original = SourceFile(
                file_name=cfg.original_path,
                folder_path=ctx.state.repo_path,
                compiler_tool=CompilerTool(cfg.compiler),
            )
            (ctx.state.repo_path / BUILD_ROOT).mkdir(parents=True, exist_ok=True)
            original.compile(
                kwds=cfg.correctness_flags,
                output_file=ctx.state.repo_path / BUILD_ROOT / "original_sanity",
            )
            ctx.state.original = original
        except Exception as exc:
            ctx.state.error = (
                f"ORIGINAL CODE FAILED TO COMPILE.\n"
                f"Source {cfg.original_path} would not build with "
                f"`{cfg.compiler.value} {cfg.correctness_flags}`.\n"
                f"Check {ctx.state.config_path} - the `compiler` or `flags.correctness` "
                f"entry may be wrong, or the source path may be stale. If the source has "
                f"drifted, regenerate the config.\n"
                f"Compiler error:\n{exc}"
            )
            return "fail"

        failures: list[str] = []
        for args, expected in cfg.golden_outputs:
            try:
                original.execute(
                    args=args,
                    validator=FunctionalValidator(
                        args=args, golden_output=expected, ret_code=0
                    ),
                )
            except (WrongOutput, WrongRetCode) as exc:
                actual = original.get_last_execution_report()
                actual_stdout = getattr(actual, "stdout", None)
                if actual_stdout is None:
                    completed = original.exec_tool.run(args=args)
                    actual_stdout = completed.stdout
                failures.append(
                    f"  args={args!r}\n"
                    f"    expected: {expected!r}\n"
                    f"    got:      {actual_stdout!r}\n"
                    f"    reason:   {exc}"
                )
            except Exception as exc:
                failures.append(f"  args={args!r}: unexpected error: {exc}")

        if failures:
            ctx.state.error = (
                f"ORIGINAL CODE FAILS ITS OWN UNIT TESTS.\n"
                f"{cfg.original_path} compiled cleanly but did not reproduce the golden "
                f"outputs recorded in {ctx.state.config_path}.\n"
                f"Check {ctx.state.config_path} - the golden `args`/`stdout` entries may "
                f"be stale (e.g. captured against an older build). Either fix the source "
                f"or regenerate the config before running the optimization pipeline.\n"
                f"{len(failures)}/{len(cfg.golden_outputs)} case(s) failed:\n"
                + "\n".join(failures)
            )
            return "fail"

        logger.info("sanity check passed: %d/%d cases", len(cfg.golden_outputs), len(cfg.golden_outputs))
        return "ok"

    async def dispatch_agent(
        state: RefactoringState,
        agent_name: str,
        input_path: Path,
        output_path: Path,
        extra_paths: dict[str, Path] | None = None,
        extra_notes: str = "",
    ) -> str:
        """Dispatch a subagent that consumes one .md and writes one .md.

        `extra_paths` is rendered as additional `key: value` lines for agents
        that need more than the input/output pair (e.g. the coder needs the
        target/reference source paths). `extra_notes` is appended verbatim.
        """
        client = await _ensure_claude_client(state)
        lines = [
            f"Dispatch the '{agent_name}' subagent via the Task tool with the following task.",
            "After it finishes, relay its summary as your final response.",
            "",
            f"input file:  {input_path}",
            f"output file: {output_path}",
        ]
        if extra_paths:
            for key, value in extra_paths.items():
                lines.append(f"{key}: {value}")
        if extra_notes:
            lines += ["", extra_notes]
        return await claude_send(client, "\n".join(lines))

    @g.step
    async def bootstrap_context(
        ctx: StepContext[RefactoringState, None, object],
    ) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        lassi_dir = ctx.state.repo_path / LASSI_DIR
        lassi_dir.mkdir(parents=True, exist_ok=True)
        context_path = lassi_dir / CONTEXT_FILE
        logger.info("writing bootstrap context -> %s", context_path)
        try:
            sample_golden = "\n".join(
                f"- args={args!r}" for args, _ in cfg.golden_outputs[:5]
            )
            context_path.write_text(
                "# Pipeline Context\n\n"
                "This file is the seed instruction for the analyst-planner-coder chain.\n"
                "Every agent consumes the prior artifact and writes the next one.\n\n"
                "## Repository\n"
                f"- root: {ctx.state.repo_path}\n"
                f"- config: {ctx.state.config_path}\n\n"
                "## Target source\n"
                f"- reference (read-only): {cfg.original_path}\n"
                f"- optimization target:   {cfg.optimized_path}\n\n"
                "## Build\n"
                f"- compiler: {cfg.compiler.value}\n"
                f"- correctness flags: {cfg.correctness_flags}\n"
                f"- performance flags: {cfg.performance_flags}\n\n"
                "## Workload\n"
                f"- benchmark args: {cfg.benchmark_args!r}\n"
                f"- benchmark runs: {cfg.benchmark_runs}\n\n"
                "## Golden behavior to preserve\n"
                f"- {len(cfg.golden_outputs)} golden case(s) captured from the reference build.\n"
                f"- The optimized variant must reproduce stdout byte-for-byte for every case.\n"
                "- Sample inputs:\n"
                f"{sample_golden}\n"
            )
            ctx.state.instructions.append(context_path)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"context bootstrap failed: {exc}"
            return "fail"

    @g.step
    async def analyze(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        if not ctx.state.instructions:
            ctx.state.error = "analyze step has no prior instruction in the chain"
            return "fail"
        input_path = ctx.state.instructions[-1]
        output_path = ctx.state.repo_path / LASSI_DIR / ANALYSIS_FILE
        logger.info("dispatching analyst: %s -> %s", input_path, output_path)
        try:
            ctx.state.claude_result = await dispatch_agent(
                ctx.state, ANALYST_AGENT, input_path, output_path
            )
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise FileNotFoundError(f"analyst did not write {output_path}")
            ctx.state.instructions.append(output_path)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"analysis step failed: {exc}"
            return "fail"

    @g.step
    async def plan_refactor(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        if not ctx.state.instructions:
            ctx.state.error = "plan step has no prior instruction in the chain"
            return "fail"
        input_path = ctx.state.instructions[-1]
        output_path = ctx.state.repo_path / LASSI_DIR / PLAN_FILE
        logger.info("dispatching planner: %s -> %s", input_path, output_path)
        try:
            ctx.state.claude_result = await dispatch_agent(
                ctx.state, PLANNER_AGENT, input_path, output_path
            )
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise FileNotFoundError(f"planner did not write {output_path}")
            ctx.state.instructions.append(output_path)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"planning step failed: {exc}"
            return "fail"

    @g.step
    async def code_refactor(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        if not ctx.state.instructions:
            ctx.state.error = "code step has no prior instruction in the chain"
            return "fail"
        cfg = ctx.state.config
        input_path = ctx.state.instructions[-1]
        output_path = ctx.state.repo_path / LASSI_DIR / CHANGES_FILE
        original_full = ctx.state.repo_path / cfg.original_path
        optimized_full = ctx.state.repo_path / cfg.optimized_path
        logger.info(
            "seeding %s from %s and dispatching coder: %s -> %s",
            optimized_full, original_full, input_path, output_path,
        )
        try:
            optimized_full.parent.mkdir(parents=True, exist_ok=True)
            optimized_full.write_text(original_full.read_text())
            seed_mtime = optimized_full.stat().st_mtime

            ctx.state.claude_result = await dispatch_agent(
                ctx.state,
                CODER_AGENT,
                input_path,
                output_path,
                extra_paths={
                    "target file":    cfg.optimized_path,
                    "reference file": cfg.original_path,
                },
            )

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise FileNotFoundError(f"coder did not write {output_path}")
            if not optimized_full.exists():
                raise FileNotFoundError(f"coder removed {optimized_full}")
            if optimized_full.stat().st_mtime <= seed_mtime:
                raise RuntimeError(
                    f"coder left {optimized_full} unchanged from the seed copy of {original_full}"
                )

            ctx.state.instructions.append(output_path)
            ctx.state.optimized = SourceFile(
                file_name=cfg.optimized_path,
                folder_path=ctx.state.repo_path,
                compiler_tool=CompilerTool(cfg.compiler),
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"coding step failed: {exc}"
            return "fail"

    @g.step
    async def ready(ctx: StepContext[RefactoringState, None, object]) -> str:
        if ctx.state.claude_client is not None:
            await ctx.state.claude_client.disconnect()
            ctx.state.claude_client = None
        assert ctx.state.config is not None
        cfg = ctx.state.config
        chain = "\n".join(f"    {i}. {p}" for i, p in enumerate(ctx.state.instructions))
        return (
            "Refactoring pipeline complete.\n"
            f"  config:      {ctx.state.config_path}\n"
            f"  compiler:    {cfg.compiler.value}\n"
            f"  sources:     {cfg.original_path} -> {cfg.optimized_path}\n"
            f"  flags:       correctness={cfg.correctness_flags!r} performance={cfg.performance_flags!r}\n"
            f"  golden:      {len(cfg.golden_outputs)} cases\n"
            f"  instruction chain ({len(ctx.state.instructions)} files):\n{chain}\n"
            f"  coder note:  {ctx.state.claude_result}"
        )

    @g.step
    async def failed(ctx: StepContext[RefactoringState, None, object]) -> str:
        if ctx.state.claude_client is not None:
            await ctx.state.claude_client.disconnect()
            ctx.state.claude_client = None
        return f"Pipeline failed: {ctx.state.error}"

    load_config_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(sanity_check_original))
        .branch(g.match(TypeExpression[Missing]).to(generate_config))
        .branch(g.match(TypeExpression[Fail]).to(failed))
    )

    generate_config_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(load_config))
        .branch(g.match(TypeExpression[Fail]).to(failed))
    )

    def ok_or_fail_to(next_step):
        return (
            g.decision()
            .branch(g.match(TypeExpression[Ok]).to(next_step))
            .branch(g.match(TypeExpression[Fail]).to(failed))
        )

    g.add(
        g.edge_from(g.start_node).to(load_config),
        g.edge_from(load_config).to(load_config_decision),
        g.edge_from(generate_config).to(generate_config_decision),
        g.edge_from(sanity_check_original).to(ok_or_fail_to(bootstrap_context)),
        g.edge_from(bootstrap_context).to(ok_or_fail_to(analyze)),
        g.edge_from(analyze).to(ok_or_fail_to(plan_refactor)),
        g.edge_from(plan_refactor).to(ok_or_fail_to(code_refactor)),
        g.edge_from(code_refactor).to(ok_or_fail_to(ready)),
        g.edge_from(ready, failed).to(g.end_node),
    )

    graph = g.build()
    state = RefactoringState(config_path=config_path, repo_path=repo_path)
    result = await graph.run(state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
