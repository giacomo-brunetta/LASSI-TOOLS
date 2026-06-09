from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Literal

from pydantic_graph import GraphBuilder, StepContext, TypeExpression

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents import (
    CoderAgent,
    ConfigBuilderAgent,
    PlannerAgent,
)
from lassi.core.compiler import Compiler, CompilerTool
from lassi.core.executer import FunctionalValidator, WrongOutput, WrongRetCode
from lassi.core.source_file import SourceFile
from lassi.profiling.profiler import Timer


class _ColoredFormatter(logging.Formatter):
    """Color log lines by logger name so Claude SDK chatter stands out."""

    RESET = "\x1b[0m"
    COLORS = {
        # Claude SDK message stream (claude_send / system messages)
        "agents.utils": "\x1b[36m",                 # cyan
        # Agent dispatch lifecycle
        "agents.base": "\x1b[35m",                  # magenta
        # SDK transport / subprocess chatter
        "claude_agent_sdk": "\x1b[2;36m",           # dim cyan
    }
    LEVEL_COLORS = {
        "WARNING": "\x1b[33m",                       # yellow
        "ERROR": "\x1b[31m",                         # red
        "CRITICAL": "\x1b[1;31m",                    # bold red
    }

    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Level color wins for warnings/errors regardless of source.
        level_color = self.LEVEL_COLORS.get(record.levelname)
        if level_color:
            return f"{level_color}{msg}{self.RESET}"
        for prefix, color in self.COLORS.items():
            if record.name.startswith(prefix):
                return f"{color}{msg}{self.RESET}"
        return msg


_handler = logging.StreamHandler()
_handler.setFormatter(_ColoredFormatter("%(levelname)s:%(name)s:%(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "graph_code_test.json"
BUILD_ROOT = Path(os.environ.get("LASSI_BUILD_ROOT", ".verify/refactoring"))
LASSI_DIR = Path(os.environ.get("LASSI_ARTIFACT_DIR", "LASSI"))
CONTEXT_FILE = "00_context.md"
PLAN_FILE = "01_plan.md"
CHANGES_FILE = "02_changes.md"
CLAUDE_MODEL = "claude-opus-4-7"

# Agent instances used by this flow.
PLANNER_AGENT = PlannerAgent()
CODER_AGENT = CoderAgent()
CONFIG_BUILDER_AGENT = ConfigBuilderAgent()

Ok = Literal["ok"]
Fail = Literal["fail"]
Missing = Literal["missing"]
Giveup = Literal["giveup"]
Skip = Literal["skip"]
Continue = Literal["continue"]
Exhausted = Literal["exhausted"]


# ---------------------------------------------------------------------------
# Config + state
# ---------------------------------------------------------------------------


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
    scope: list[Path] | None  # None = unrestricted

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


@dataclass
class PipelineStage:
    config_path: Path = field(default_factory=lambda: DEFAULT_CONFIG_PATH)
    repo_path: Path = field(default_factory=lambda: Path.cwd().resolve())
    config: PipelineConfig | None = None
    original: SourceFile | None = None
    optimized: SourceFile | None = None
    llm_result: str | None = None
    instructions: list[Path] = field(default_factory=list)
    # Retry / feedback bookkeeping
    coder_iterations: int = 0
    max_coder_iterations: int = 2
    planner_iterations: int = 0
    max_planner_iterations: int = 1
    candidate_seeded: bool = False
    code_feedback: str | None = None  # fed to coder on the next dispatch
    plan_feedback: str | None = None  # fed to planner on the next dispatch
    # Profile gate
    profile_enabled: bool = True
    original_latencies: list[float] = field(default_factory=list)
    optimized_latencies: list[float] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
            "Path to the pipeline config JSON. If the file does not exist, an "
            "agent will be asked to generate it from the repo contents."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repo to operate on (default: current working directory).",
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Skip the profile step (only run unit-test verification).",
    )
    return parser.parse_args(argv)


def _session_kwargs(state: PipelineStage) -> dict:
    """Common per-agent session kwargs (cwd, allowed_paths, model)."""
    allowed_paths = (
        state.config.resolved_scope(state.repo_path) if state.config else None
    )
    if allowed_paths is not None:
        allowed_paths.append((state.repo_path / LASSI_DIR).resolve())
    return {
        "cwd": state.repo_path,
        "allowed_paths": allowed_paths,
        "model": CLAUDE_MODEL,
    }


def _benchmark(source: SourceFile, args: str, runs: int) -> list[float]:
    latencies: list[float] = []
    for _ in range(runs):
        report = source.execute(args=args, profiler=Timer())
        latencies.append(report.latency)
    return latencies


def _ensure_candidate_seeded(
    original_path: Path,
    optimized_path: Path,
    *,
    already_seeded: bool,
) -> bool:
    """Seed the candidate once, preserving it across retries and re-plans."""
    optimized_path.parent.mkdir(parents=True, exist_ok=True)
    if not already_seeded:
        optimized_path.write_bytes(original_path.read_bytes())
    return True


def _gcovr_summary(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["gcovr", "--root", str(root), "--print-summary"],
            capture_output=True, text=True, timeout=30,
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
            result.returncode, (result.stderr or "").strip(),
        )
        return None
    return result.stdout.strip()


def _format_golden_failure(args: str, expected: str, actual: str, exc: Exception) -> str:
    return (
        f"  args={args!r}\n"
        f"    expected: {expected!r}\n"
        f"    got:      {actual!r}\n"
        f"    reason:   {exc}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config_path = args.config_path.resolve()
    repo_path = (args.repo or Path.cwd()).resolve()

    g = GraphBuilder(state_type=PipelineStage, output_type=str)

    @g.step
    async def load_config(ctx: StepContext[PipelineStage, None, object]) -> Ok | Missing | Fail:
        cfg_path = ctx.state.config_path
        if not cfg_path.exists():
            logger.info("config %s not found; will ask agent to generate it", cfg_path)
            return "missing"
        try:
            ctx.state.config = PipelineConfig.load(cfg_path)
            logger.info(
                "loaded config from %s: compiler=%s sources=(%s -> %s) golden_cases=%d target_speedup=%.2f%%",
                cfg_path,
                ctx.state.config.compiler.value,
                ctx.state.config.original_path,
                ctx.state.config.optimized_path,
                len(ctx.state.config.golden_outputs),
                ctx.state.config.target_speedup,
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"failed to parse config {cfg_path}: {exc}"
            return "fail"

    @g.step
    async def generate_config(ctx: StepContext[PipelineStage, None, object]) -> Ok | Fail:
        cfg_path = ctx.state.config_path
        repo = ctx.state.repo_path
        logger.info("asking config-builder to generate %s for repo %s", cfg_path, repo)
        try:
            ctx.state.llm_result = await CONFIG_BUILDER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                repo_path=repo,
                output_path=cfg_path,
            )
            if not cfg_path.exists():
                raise FileNotFoundError(f"agent did not create {cfg_path}")
            json.loads(cfg_path.read_text())  # parse-validate
            return "ok"
        except Exception as exc:
            ctx.state.error = f"config generation failed: {exc}"
            return "fail"

    @g.step
    async def sanity_check_original(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info(
            "sanity-checking original (%s) against %d golden case(s)",
            cfg.original_path, len(cfg.golden_outputs),
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
                f"Check {ctx.state.config_path}.\nCompiler error:\n{exc}"
            )
            return "fail"

        failures: list[str] = []
        for golden_args, expected in cfg.golden_outputs:
            try:
                original.execute(
                    args=golden_args,
                    validator=FunctionalValidator(
                        args=golden_args, golden_output=expected, ret_code=0
                    ),
                )
            except (WrongOutput, WrongRetCode) as exc:
                actual = original.get_last_execution_report()
                actual_stdout = getattr(actual, "stdout", None)
                if actual_stdout is None:
                    completed = original.exec_tool.run(args=golden_args)
                    actual_stdout = completed.stdout
                failures.append(_format_golden_failure(golden_args, expected, actual_stdout, exc))
            except Exception as exc:
                failures.append(f"  args={golden_args!r}: unexpected error: {exc}")

        if failures:
            ctx.state.error = (
                f"ORIGINAL CODE FAILS ITS OWN UNIT TESTS.\n"
                f"{len(failures)}/{len(cfg.golden_outputs)} case(s) failed:\n"
                + "\n".join(failures)
            )
            return "fail"

        logger.info(
            "sanity check passed: %d/%d cases",
            len(cfg.golden_outputs), len(cfg.golden_outputs),
        )
        return "ok"

    @g.step
    async def bootstrap_context(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        lassi_dir = ctx.state.repo_path / LASSI_DIR
        lassi_dir.mkdir(parents=True, exist_ok=True)
        context_path = lassi_dir / CONTEXT_FILE
        logger.info("writing bootstrap context -> %s", context_path)
        try:
            sample_golden = "\n".join(
                f"- args={a!r}" for a, _ in cfg.golden_outputs[:5]
            )
            context_path.write_text(
                "# Pipeline Context\n\n"
                "This file is the seed instruction for the planner-coder chain.\n"
                "The planner inspects the source and produces one actionable plan.\n\n"
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
                f"- benchmark runs: {cfg.benchmark_runs}\n"
                f"- target speedup (strict, %): > {cfg.target_speedup:.2f}\n\n"
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
    async def plan_refactor(ctx: StepContext[PipelineStage, None, object]) -> Ok | Fail:
        if not ctx.state.instructions:
            ctx.state.error = "plan step has no prior instruction in the chain"
            return "fail"
        input_path = ctx.state.repo_path / LASSI_DIR / CONTEXT_FILE
        output_path = ctx.state.repo_path / LASSI_DIR / PLAN_FILE
        notes = ctx.state.plan_feedback or ""
        if notes:
            logger.info(
                "re-planning (round %d/%d) with feedback:\n%s",
                ctx.state.planner_iterations,
                ctx.state.max_planner_iterations,
                notes,
            )
        logger.info("dispatching planner: %s -> %s", input_path, output_path)
        try:
            ctx.state.llm_result = await PLANNER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                input_path=input_path,
                output_path=output_path,
                notes=notes,
            )
            if not output_path.exists() or output_path.stat().st_size == 0:
                raise FileNotFoundError(f"planner did not write {output_path}")
            ctx.state.instructions.append(output_path)
            # A fresh plan gets a fresh retry budget but keeps the candidate so
            # the planner and coder can build on useful work from prior rounds.
            ctx.state.plan_feedback = None
            ctx.state.code_feedback = None
            ctx.state.coder_iterations = 0
            return "ok"
        except Exception as exc:
            ctx.state.error = f"planning step failed: {exc}"
            return "fail"

    @g.step
    async def code_refactor(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Giveup | Fail:
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        cfg = ctx.state.config
        plan_path = ctx.state.repo_path / LASSI_DIR / PLAN_FILE
        input_path = plan_path if plan_path.exists() else ctx.state.instructions[-1]
        output_path = ctx.state.repo_path / LASSI_DIR / CHANGES_FILE
        original_full = ctx.state.repo_path / cfg.original_path
        optimized_full = ctx.state.repo_path / cfg.optimized_path
        notes = ctx.state.code_feedback or ""
        if notes:
            logger.info(
                "coder retry round %d/%d with feedback:\n%s",
                ctx.state.coder_iterations,
                ctx.state.max_coder_iterations,
                notes,
            )
        logger.info(
            "dispatching coder against candidate %s: %s -> %s",
            optimized_full, input_path, output_path,
        )
        try:
            ctx.state.candidate_seeded = _ensure_candidate_seeded(
                original_full,
                optimized_full,
                already_seeded=ctx.state.candidate_seeded,
            )
            candidate_before = optimized_full.read_bytes()

            ctx.state.llm_result = await CODER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                input_path=input_path,
                output_path=output_path,
                target_file=cfg.optimized_path,
                reference_file=cfg.original_path,
                notes=notes,
            )

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise FileNotFoundError(f"coder did not write {output_path}")
            if not optimized_full.exists():
                raise FileNotFoundError(f"coder removed {optimized_full}")
            if optimized_full.read_bytes() == candidate_before:
                # An unchanged candidate means the coder found no actionable
                # repair or implementation for the current plan.
                ctx.state.plan_feedback = (
                    f"Coder did not modify {cfg.optimized_path}. The plan at "
                    f"{plan_path} appears unactionable to the coder.\n"
                    f"Coder report ({output_path}): {ctx.state.llm_result}"
                )
                logger.warning("coder gave up; escalating to planner")
                return "giveup"

            ctx.state.instructions.append(output_path)
            ctx.state.optimized = SourceFile(
                file_name=cfg.optimized_path,
                folder_path=ctx.state.repo_path,
                compiler_tool=CompilerTool(cfg.compiler),
            )
            # Feedback consumed; clear for the next iteration if any.
            ctx.state.code_feedback = None
            return "ok"
        except Exception as exc:
            ctx.state.error = f"coding step failed (technical): {exc}"
            return "fail"

    @g.step
    async def test_refactor(ctx: StepContext[PipelineStage, None, object]) -> Ok | Fail:
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        assert ctx.state.optimized is not None
        cfg = ctx.state.config
        cov_flags = f"{cfg.correctness_flags} --coverage"
        logger.info(
            "test_refactor: building original (%s) + optimized (%s)",
            cfg.correctness_flags, cov_flags,
        )
        # Stale .gcno/.gcda from a prior compile poisons gcovr (0% reports
        # when the new source line count differs). Wipe before re-instrumenting.
        for stale in ctx.state.repo_path.glob("*.gcno"):
            stale.unlink()
        for stale in ctx.state.repo_path.glob("*.gcda"):
            stale.unlink()
        try:
            ctx.state.original.compile(
                kwds=cfg.correctness_flags,
                output_file=ctx.state.repo_path / BUILD_ROOT / "original_correctness",
            )
            ctx.state.optimized.compile(
                kwds=cov_flags,
                output_file=ctx.state.repo_path / BUILD_ROOT / "optimized_correctness",
            )
        except Exception as exc:
            ctx.state.code_feedback = (
                f"The optimized variant {cfg.optimized_path} did not compile with "
                f"`{cfg.compiler.value} {cov_flags}`:\n{exc}\n"
                f"Fix the compile error before changing anything else."
            )
            return "fail"

        failures: list[str] = []
        for golden_args, expected in cfg.golden_outputs:
            try:
                ctx.state.optimized.execute(
                    args=golden_args,
                    validator=FunctionalValidator(
                        args=golden_args, golden_output=expected, ret_code=0
                    ),
                )
            except (WrongOutput, WrongRetCode) as exc:
                actual = ctx.state.optimized.get_last_execution_report()
                actual_stdout = getattr(actual, "stdout", None)
                if actual_stdout is None:
                    completed = ctx.state.optimized.exec_tool.run(args=golden_args)
                    actual_stdout = completed.stdout
                failures.append(_format_golden_failure(golden_args, expected, actual_stdout, exc))
            except Exception as exc:
                failures.append(f"  args={golden_args!r}: unexpected error: {exc}")

        summary = _gcovr_summary(ctx.state.repo_path)
        if summary:
            logger.info("optimized coverage (gcovr):\n%s", summary)

        if failures:
            ctx.state.code_feedback = (
                f"Unit tests failed for {cfg.optimized_path}: "
                f"{len(failures)}/{len(cfg.golden_outputs)} case(s) diverged from "
                f"the reference stdout:\n"
                + "\n".join(failures)
                + "\nFix the divergences. Keep the CLI and exact stdout intact."
            )
            return "fail"

        logger.info(
            "unit tests passed: %d/%d cases",
            len(cfg.golden_outputs), len(cfg.golden_outputs),
        )
        return "ok"

    @g.step
    async def profile_refactor(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Fail | Skip:
        if not ctx.state.profile_enabled:
            logger.info("profile step disabled; skipping")
            return "skip"
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        assert ctx.state.optimized is not None
        cfg = ctx.state.config
        logger.info(
            "profile_refactor: rebuilding both at %s and benchmarking with args %r over %d runs",
            cfg.performance_flags, cfg.benchmark_args, cfg.benchmark_runs,
        )
        try:
            ctx.state.original.compile(
                kwds=cfg.performance_flags,
                output_file=ctx.state.repo_path / BUILD_ROOT / "original_perf",
            )
            ctx.state.optimized.compile(
                kwds=cfg.performance_flags,
                output_file=ctx.state.repo_path / BUILD_ROOT / "optimized_perf",
            )
        except Exception as exc:
            ctx.state.code_feedback = (
                f"The optimized variant {cfg.optimized_path} did not compile with "
                f"`{cfg.compiler.value} {cfg.performance_flags}`:\n{exc}"
            )
            return "fail"
        try:
            ctx.state.original_latencies = _benchmark(
                ctx.state.original, cfg.benchmark_args, cfg.benchmark_runs,
            )
            ctx.state.optimized_latencies = _benchmark(
                ctx.state.optimized, cfg.benchmark_args, cfg.benchmark_runs,
            )
        except Exception as exc:
            ctx.state.code_feedback = f"Benchmark execution failed: {exc}"
            return "fail"

        original = mean(ctx.state.original_latencies)
        optimized = mean(ctx.state.optimized_latencies)
        if optimized <= 0:
            ctx.state.code_feedback = f"Invalid optimized latency: {optimized}"
            return "fail"
        speedup = original / optimized
        speedup_pct = (speedup - 1.0) * 100.0
        logger.info(
            "profile: original=%.6fs optimized=%.6fs speedup=%.3fx (%.2f%%) target>%.2f%%",
            original, optimized, speedup, speedup_pct, cfg.target_speedup,
        )
        if speedup_pct > cfg.target_speedup:
            return "ok"
        ctx.state.code_feedback = (
            f"Speedup {speedup_pct:.2f}% did not exceed target "
            f"{cfg.target_speedup:.2f}% (original={original:.6f}s, "
            f"optimized={optimized:.6f}s). Pick a different optimization that "
            f"actually moves the runtime."
        )
        return "fail"

    @g.step
    async def coder_retry_gate(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Continue | Exhausted:
        if ctx.state.coder_iterations < ctx.state.max_coder_iterations:
            ctx.state.coder_iterations += 1
            logger.info(
                "coder retry %d/%d (test/profile feedback queued)",
                ctx.state.coder_iterations, ctx.state.max_coder_iterations,
            )
            return "continue"
        logger.warning(
            "coder exhausted after %d retries; escalating to planner",
            ctx.state.coder_iterations,
        )
        ctx.state.plan_feedback = (
            f"Coder exhausted {ctx.state.coder_iterations} retries on the current plan. "
            f"Last coder feedback was:\n{ctx.state.code_feedback}\n"
            f"Revise the plan: either pick a different strategy or weaken the "
            f"expected impact."
        )
        return "exhausted"

    @g.step
    async def plan_retry_gate(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Continue | Exhausted:
        if ctx.state.planner_iterations < ctx.state.max_planner_iterations:
            ctx.state.planner_iterations += 1
            logger.info(
                "planner retry %d/%d (coder/test feedback queued)",
                ctx.state.planner_iterations, ctx.state.max_planner_iterations,
            )
            return "continue"
        ctx.state.error = (
            f"Pipeline failed: planner exhausted {ctx.state.planner_iterations} "
            f"retries (with {ctx.state.max_coder_iterations} coder retries each). "
            f"Last plan feedback:\n{ctx.state.plan_feedback}"
        )
        return "exhausted"

    @g.step
    async def ready(ctx: StepContext[PipelineStage, None, object]) -> str:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        chain = "\n".join(f"    {i}. {p}" for i, p in enumerate(ctx.state.instructions))
        perf_line = ""
        if ctx.state.optimized_latencies:
            original = mean(ctx.state.original_latencies)
            optimized = mean(ctx.state.optimized_latencies)
            speedup = original / optimized if optimized else float("inf")
            speedup_pct = (speedup - 1.0) * 100.0
            perf_line = (
                f"  perf:        original={original:.6f}s "
                f"optimized={optimized:.6f}s speedup={speedup:.3f}x "
                f"({speedup_pct:+.2f}%)\n"
            )
        return (
            "Refactoring pipeline complete.\n"
            f"  config:      {ctx.state.config_path}\n"
            f"  compiler:    {cfg.compiler.value}\n"
            f"  sources:     {cfg.original_path} -> {cfg.optimized_path}\n"
            f"  flags:       correctness={cfg.correctness_flags!r} "
            f"performance={cfg.performance_flags!r}\n"
            f"  golden:      {len(cfg.golden_outputs)} cases\n"
            f"  planner:     {ctx.state.planner_iterations} re-plan round(s)\n"
            f"  coder:       {ctx.state.coder_iterations} retry round(s)\n"
            + perf_line
            + f"  artifact chain ({len(ctx.state.instructions)} files):\n{chain}\n"
            f"  coder note:  {ctx.state.llm_result}"
        )

    @g.step
    async def failed(ctx: StepContext[PipelineStage, None, object]) -> str:
        return f"Pipeline failed: {ctx.state.error}"

    # ----- decisions -----

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

    code_refactor_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(test_refactor))
        .branch(g.match(TypeExpression[Giveup]).to(plan_retry_gate))
        .branch(g.match(TypeExpression[Fail]).to(failed))
    )

    test_refactor_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(profile_refactor))
        .branch(g.match(TypeExpression[Fail]).to(coder_retry_gate))
    )

    profile_refactor_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(ready))
        .branch(g.match(TypeExpression[Skip]).to(ready))
        .branch(g.match(TypeExpression[Fail]).to(coder_retry_gate))
    )

    coder_retry_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Continue]).to(code_refactor))
        .branch(g.match(TypeExpression[Exhausted]).to(plan_retry_gate))
    )

    plan_retry_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Continue]).to(plan_refactor))
        .branch(g.match(TypeExpression[Exhausted]).to(failed))
    )

    # ----- edges -----

    g.add(
        g.edge_from(g.start_node).to(load_config),
        g.edge_from(load_config).to(load_config_decision),
        g.edge_from(generate_config).to(generate_config_decision),
        g.edge_from(sanity_check_original).to(ok_or_fail_to(bootstrap_context)),
        g.edge_from(bootstrap_context).to(ok_or_fail_to(plan_refactor)),
        g.edge_from(plan_refactor).to(ok_or_fail_to(code_refactor)),
        g.edge_from(code_refactor).to(code_refactor_decision),
        g.edge_from(test_refactor).to(test_refactor_decision),
        g.edge_from(profile_refactor).to(profile_refactor_decision),
        g.edge_from(coder_retry_gate).to(coder_retry_decision),
        g.edge_from(plan_retry_gate).to(plan_retry_decision),
        g.edge_from(ready, failed).to(g.end_node),
    )

    graph = g.build()
    state = PipelineStage(
        config_path=config_path,
        repo_path=repo_path,
        profile_enabled=not args.no_profile,
    )
    # print(graph.render())

    result = await graph.run(state=state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
