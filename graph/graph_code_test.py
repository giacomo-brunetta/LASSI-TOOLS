from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Literal

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from pydantic_graph import GraphBuilder, StepContext, TypeExpression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from agents import CCodeOptimizerAgent, PlannerAgent, build_permission_router
from lassi.core.compiler import Compiler, CompilerTool
from lassi.core.executer import FunctionalValidator, WrongOutput
from lassi.core.source_file import SourceFile
from lassi.profiling.profiler import Timer
from lassi.verification.checks import parse_floats_from_text, summarize_numeric_diff


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "graph_code_test.json"
BUILD_ROOT = Path(".verify/refactoring")
CLAUDE_MODEL = "claude-opus-4-7"
MAX_FEEDBACK_ITERATIONS = 3
MAX_PLAN_ITERATIONS = 3

c_optimizer_agent = CCodeOptimizerAgent()
planner_agent = PlannerAgent()
AGENT_REGISTRY = dict([
    c_optimizer_agent.registration(),
    planner_agent.registration(),
])

Ok = Literal["ok"]
Fail = Literal["fail"]


@dataclass
class PipelineConfig:
    original_path: Path
    optimized_path: Path
    compiler: Compiler
    correctness_flags: str
    performance_flags: str
    benchmark_args: str
    benchmark_runs: int
    target_speedup: float
    golden_outputs: list[tuple[str, str]]
    scope: list[Path] | None  # None = unrestricted, [] = deny all file ops

    @classmethod
    def load(cls, path: Path) -> PipelineConfig:
        raw = json.loads(path.read_text())
        sources = raw["sources"]
        flags = raw["flags"]
        args = raw["arguments"]
        golden = [(case["args"], case["stdout"]) for case in args.get("golden", [])]
        scope = [Path(p) for p in raw["scope"]] if "scope" in raw else None
        return cls(
            original_path=Path(sources["original"]),
            optimized_path=Path(sources["optimized"]),
            compiler=Compiler(raw["compiler"]),
            correctness_flags=flags["correctness"],
            performance_flags=flags["performance"],
            benchmark_args=args["benchmark"],
            benchmark_runs=int(args.get("benchmark_runs", 5)),
            target_speedup=float(args.get("target_speedup", 0.0)),
            golden_outputs=golden,
            scope=scope,
        )

    def resolved_scope(self, cwd: Path) -> list[Path] | None:
        if self.scope is None:
            return None
        return [(cwd / p).resolve() for p in self.scope]


def make_source(path: Path, compiler: Compiler) -> SourceFile:
    return SourceFile(path, compiler_tool=CompilerTool(compiler))


def validate_golden_outputs(
    source: SourceFile, label: str, golden_outputs: list[tuple[str, str]]
) -> None:
    for args, golden_output in golden_outputs:
        completed = source.execute(validator=FunctionalValidator(args=args, ret_code=0))
        try:
            FunctionalValidator(golden_output=golden_output, ret_code=0).validate(completed)
        except WrongOutput as exc:
            diff = summarize_numeric_diff(
                parse_floats_from_text(completed.stdout),
                parse_floats_from_text(golden_output),
            )
            raise AssertionError(
                f"{label} output mismatch for args {args!r}\n"
                f"expected stdout:\n{golden_output}"
                f"actual stdout:\n{completed.stdout}"
                f"numeric diff: {json.dumps(diff, sort_keys=True)}"
            ) from exc


def benchmark(source: SourceFile, args: str, runs: int) -> list[float]:
    latencies = []
    for _ in range(runs):
        report = source.execute(args=args, profiler=Timer())
        latencies.append(report.latency)
    return latencies


def gcovr_summary(root: Path) -> str | None:
    """Run `gcovr --print-summary` against `root` and return its stdout.

    Returns None if gcovr is missing or exits non-zero. Coverage data
    (.gcno/.gcda) must already have been produced by a `--coverage`-compiled
    binary executing inside `root`.
    """
    try:
        result = subprocess.run(
            ["gcovr", "--root", str(root), "--print-summary"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        logger.warning("gcovr is not installed; skipping coverage report")
        return None
    except Exception as exc:
        logger.warning("gcovr invocation raised: %s", exc)
        return None
    if result.returncode != 0:
        logger.warning(
            "gcovr exited %d: %s",
            result.returncode,
            (result.stderr or "").strip(),
        )
        return None
    return result.stdout.strip()


@dataclass
class RefactoringState:
    config_path: Path = field(default_factory=lambda: DEFAULT_CONFIG_PATH)
    repo_path: Path = field(default_factory=lambda: Path.cwd().resolve())
    config: PipelineConfig | None = None
    original: SourceFile | None = None
    optimized: SourceFile | None = None
    claude_client: ClaudeSDKClient | None = field(default=None, repr=False)
    claude_result: str | None = None
    correctness_passed: bool = False
    original_latencies: list[float] = field(default_factory=list)
    optimized_latencies: list[float] = field(default_factory=list)
    feedback_iterations: int = 0
    plan_iterations: int = 0
    error: str | None = None


async def main() -> None:
    g = GraphBuilder(state_type=RefactoringState, output_type=str)

    @g.step
    async def prepare_sources(ctx: StepContext[RefactoringState, None, None]) -> Ok | Fail:
        logger.info("loading pipeline config from %s", ctx.state.config_path)
        try:
            cfg = PipelineConfig.load(ctx.state.config_path)
            ctx.state.config = cfg
            logger.info(
                "config: compiler=%s sources=(%s -> %s) flags=(%s/%s) bench_args=%r",
                cfg.compiler.value,
                cfg.original_path,
                cfg.optimized_path,
                cfg.correctness_flags,
                cfg.performance_flags,
                cfg.benchmark_args,
            )
            ctx.state.original = make_source(cfg.original_path, cfg.compiler)
            ctx.state.optimized = make_source(cfg.optimized_path, cfg.compiler)
            ctx.state.optimized.write(ctx.state.original.read())
            BUILD_ROOT.mkdir(parents=True, exist_ok=True)
            allowed_paths = cfg.resolved_scope(ctx.state.repo_path)
            logger.info(
                "permission scope: %s",
                [str(p) for p in allowed_paths] if allowed_paths is not None else "<unrestricted>",
            )
            options = ClaudeAgentOptions(
                cwd=str(ctx.state.repo_path),
                model=CLAUDE_MODEL,
                permission_mode="acceptEdits",
                allowed_tools=[
                    "Read", "Write", "Edit", "Bash", "Glob", "Grep", "Task", "Skill",
                ],
                agents=AGENT_REGISTRY,
                can_use_tool=build_permission_router(
                    allowed_paths=allowed_paths,
                    agents={
                        c_optimizer_agent.name: c_optimizer_agent,
                        planner_agent.name: planner_agent,
                    },
                ),
            )
            client = ClaudeSDKClient(options=options)
            await client.connect()
            ctx.state.claude_client = client
            return "ok"
        except Exception as exc:
            ctx.state.error = f"source preparation failed: {exc}"
            return "fail"

    @g.step
    async def refactor_with_claude(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info("asking Claude to optimize %s", cfg.optimized_path)
        try:
            assert ctx.state.claude_client is not None
            ctx.state.claude_result = await c_optimizer_agent.dispatch_agent(
                ctx.state.claude_client,
                optimized_path=cfg.optimized_path,
                original_path=cfg.original_path,
                compiler=cfg.compiler.value,
                performance_flags=cfg.performance_flags,
            )
            if not cfg.optimized_path.exists():
                raise FileNotFoundError(f"Claude did not create {cfg.optimized_path}")
            ctx.state.optimized = make_source(cfg.optimized_path, cfg.compiler)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"Claude refactoring failed: {exc}"
            return "fail"

    @g.step
    async def check_correctness(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        optimized_correctness_flags = f"{cfg.correctness_flags} --coverage"
        logger.info(
            "checking correctness with %s %s (optimized: %s)",
            cfg.compiler.value,
            cfg.correctness_flags,
            optimized_correctness_flags,
        )
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original.compile(
                kwds=cfg.correctness_flags, output_file=BUILD_ROOT / "original_correctness"
            )
            ctx.state.optimized.compile(
                kwds=optimized_correctness_flags,
                output_file=BUILD_ROOT / "optimized_correctness",
            )
            validate_golden_outputs(ctx.state.original, "original", cfg.golden_outputs)
            validate_golden_outputs(ctx.state.optimized, "optimized", cfg.golden_outputs)
            summary = gcovr_summary(ctx.state.repo_path)
            if summary:
                logger.info("optimized coverage (gcovr):\n%s", summary)
            ctx.state.correctness_passed = True
            return "ok"
        except Exception as exc:
            ctx.state.error = f"correctness check failed: {exc}"
            return "fail"

    @g.step
    async def compile_perf(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info("compiling with %s %s", cfg.compiler.value, cfg.performance_flags)
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original.compile(
                kwds=cfg.performance_flags, output_file=BUILD_ROOT / "original_perf"
            )
            ctx.state.optimized.compile(
                kwds=cfg.performance_flags, output_file=BUILD_ROOT / "optimized_perf"
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"performance compilation failed: {exc}"
            return "fail"

    @g.step
    async def benchmark_latency(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info(
            "benchmarking %s %s with args %r over %d runs",
            cfg.compiler.value,
            cfg.performance_flags,
            cfg.benchmark_args,
            cfg.benchmark_runs,
        )
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original_latencies = benchmark(
                ctx.state.original, cfg.benchmark_args, cfg.benchmark_runs
            )
            ctx.state.optimized_latencies = benchmark(
                ctx.state.optimized, cfg.benchmark_args, cfg.benchmark_runs
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"latency benchmark failed: {exc}"
            return "fail"

    @g.step
    async def check_speedup(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        if not ctx.state.original_latencies or not ctx.state.optimized_latencies:
            ctx.state.error = "speedup check ran without latency samples"
            return "fail"
        original = mean(ctx.state.original_latencies)
        optimized = mean(ctx.state.optimized_latencies)
        if optimized <= 0:
            ctx.state.error = f"invalid optimized latency: {optimized}"
            return "fail"
        speedup = original / optimized
        speedup_pct = (speedup - 1.0) * 100.0
        logger.info(
            "speedup gate: original=%.6fs optimized=%.6fs speedup=%.3fx (%.2f%%) target>%.2f%%",
            original,
            optimized,
            speedup,
            speedup_pct,
            cfg.target_speedup,
        )
        if speedup_pct > cfg.target_speedup:
            return "ok"
        ctx.state.error = (
            f"speedup {speedup_pct:.2f}% did not exceed target {cfg.target_speedup:.2f}% "
            f"(original={original:.6f}s, optimized={optimized:.6f}s)"
        )
        return "fail"

    @g.step
    async def replan_with_planner(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        ctx.state.plan_iterations += 1
        if ctx.state.plan_iterations > MAX_PLAN_ITERATIONS:
            ctx.state.error = (
                f"exhausted {MAX_PLAN_ITERATIONS} plan rounds; last: {ctx.state.error}"
            )
            return "fail"
        logger.info(
            "plan round %d/%d: dispatching '%s' then '%s'",
            ctx.state.plan_iterations,
            MAX_PLAN_ITERATIONS,
            planner_agent.name,
            c_optimizer_agent.name,
        )
        try:
            assert ctx.state.claude_client is not None
            original = mean(ctx.state.original_latencies)
            optimized = mean(ctx.state.optimized_latencies)
            strategy = await planner_agent.dispatch_agent(
                ctx.state.claude_client,
                original_path=cfg.original_path,
                optimized_path=cfg.optimized_path,
                original_latency=original,
                optimized_latency=optimized,
                target_speedup=cfg.target_speedup,
            )
            logger.info("planner returned strategy (%d chars)", len(strategy))
            ctx.state.claude_result = await c_optimizer_agent.dispatch_agent(
                ctx.state.claude_client,
                optimized_path=cfg.optimized_path,
                original_path=cfg.original_path,
                compiler=cfg.compiler.value,
                performance_flags=cfg.performance_flags,
                strategy=strategy,
            )
            if not cfg.optimized_path.exists():
                raise FileNotFoundError(f"replan removed {cfg.optimized_path}")
            ctx.state.optimized = make_source(cfg.optimized_path, cfg.compiler)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"replan failed: {exc}"
            return "fail"

    @g.step
    async def send_error_feedback(ctx: StepContext[RefactoringState, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        ctx.state.feedback_iterations += 1
        if ctx.state.feedback_iterations > MAX_FEEDBACK_ITERATIONS:
            ctx.state.error = (
                f"exhausted {MAX_FEEDBACK_ITERATIONS} repair rounds; last error: {ctx.state.error}"
            )
            return "fail"
        logger.info(
            "repair round %d/%d: sending error back to Claude",
            ctx.state.feedback_iterations,
            MAX_FEEDBACK_ITERATIONS,
        )
        try:
            assert ctx.state.claude_client is not None
            ctx.state.claude_result = await c_optimizer_agent.dispatch_agent(
                ctx.state.claude_client,
                optimized_path=cfg.optimized_path,
                original_path=cfg.original_path,
                compiler=cfg.compiler.value,
                performance_flags=cfg.performance_flags,
                error=ctx.state.error,
            )
            if not cfg.optimized_path.exists():
                raise FileNotFoundError(f"Claude removed {cfg.optimized_path}")
            ctx.state.optimized = make_source(cfg.optimized_path, cfg.compiler)
            return "ok"
        except Exception as exc:
            ctx.state.error = f"Claude follow-up failed: {exc}"
            return "fail"

    @g.step
    async def success(ctx: StepContext[RefactoringState, None, object]) -> str:
        if ctx.state.claude_client is not None:
            await ctx.state.claude_client.disconnect()
            ctx.state.claude_client = None
        assert ctx.state.config is not None
        cfg = ctx.state.config
        original = mean(ctx.state.original_latencies)
        optimized = mean(ctx.state.optimized_latencies)
        speedup = original / optimized if optimized else float("inf")
        speedup_pct = (speedup - 1.0) * 100.0
        return (
            "Refactoring passed correctness and speedup gates.\n"
            f"Repair rounds used: {ctx.state.feedback_iterations}\n"
            f"Plan rounds used: {ctx.state.plan_iterations}\n"
            f"Original ({cfg.performance_flags}) mean latency: {original:.6f} s\n"
            f"Optimized ({cfg.performance_flags}) mean latency: {optimized:.6f} s\n"
            f"Speedup: {speedup:.3f}x ({speedup_pct:+.2f}%, target >{cfg.target_speedup:.2f}%)\n"
            f"Claude summary: {ctx.state.claude_result}"
        )

    @g.step
    async def failed(ctx: StepContext[RefactoringState, None, object]) -> str:
        if ctx.state.claude_client is not None:
            await ctx.state.claude_client.disconnect()
            ctx.state.claude_client = None
        return f"Refactoring pipeline failed: {ctx.state.error}"

    def branch_with_feedback(next_step):
        return (
            g.decision()
            .branch(g.match(TypeExpression[Ok]).to(next_step))
            .branch(g.match(TypeExpression[Fail]).to(send_error_feedback))
        )

    def branch_terminal(next_step):
        return (
            g.decision()
            .branch(g.match(TypeExpression[Ok]).to(next_step))
            .branch(g.match(TypeExpression[Fail]).to(failed))
        )

    def branch_to_replan(next_step):
        return (
            g.decision()
            .branch(g.match(TypeExpression[Ok]).to(next_step))
            .branch(g.match(TypeExpression[Fail]).to(replan_with_planner))
        )

    g.add(
        g.edge_from(g.start_node).to(prepare_sources),
        g.edge_from(prepare_sources).to(branch_terminal(refactor_with_claude)),
        g.edge_from(refactor_with_claude).to(branch_with_feedback(check_correctness)),
        g.edge_from(check_correctness).to(branch_with_feedback(compile_perf)),
        g.edge_from(compile_perf).to(branch_with_feedback(benchmark_latency)),
        g.edge_from(benchmark_latency).to(branch_with_feedback(check_speedup)),
        g.edge_from(check_speedup).to(branch_to_replan(success)),
        g.edge_from(replan_with_planner).to(branch_terminal(check_correctness)),
        g.edge_from(send_error_feedback).to(branch_terminal(check_correctness)),
        g.edge_from(success, failed).to(g.end_node),
    )

    graph = g.build()
    config_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    state = RefactoringState(config_path=config_path)
    result = await graph.run(state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
