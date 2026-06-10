from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
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
from graph.container_pool import (
    AgentContainer,
    CONTAINER_REFERENCE,
    CONTAINER_WORKSPACE,
    DEFAULT_IMAGE,
    EXTERNAL_CONFIG_MOUNT,
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
REFERENCE_ROOT = Path(os.environ.get("LASSI_REFERENCE_ROOT", "."))
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
        original_path = _project_relative_path(sources["original"], "sources.original")
        optimized_path = _project_relative_path(sources["optimized"], "sources.optimized")
        if original_path == optimized_path:
            raise ValueError("sources.original and sources.optimized must be different paths")
        scope = (
            [_project_relative_path(p, "scope entry") for p in raw["scope"]]
            if "scope" in raw
            else None
        )
        return cls(
            original_path=original_path,
            optimized_path=optimized_path,
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
    context_message: str | None = None
    plan_message: str | None = None
    coder_report: str | None = None
    reports: list[tuple[str, str]] = field(default_factory=list)
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


def _project_relative_path(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a project-relative path: {value!r}")
    return path


def _resolve_config_path(repo_path: Path, config_path: Path) -> Path:
    if config_path.is_absolute():
        return config_path.resolve()
    return (repo_path / config_path).resolve()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the graph-based refactoring pipeline against a pipeline config.",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        type=Path,
        default=None,
        help="Project directory to operate on (default: current working directory).",
    )
    parser.add_argument(
        "--generate-config-only",
        action="store_true",
        help=argparse.SUPPRESS,
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
        "--no-profile",
        action="store_true",
        help="Skip the profile step (only run unit-test verification).",
    )
    parser.add_argument(
        "--no-docker",
        action="store_true",
        help=(
            "Run the graph, agents, compilation, and benchmarks directly on the "
            "host. Default is Docker."
        ),
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help="Docker image used for graph execution (default: %(default)s).",
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=Path.home() / ".claude" / "settings.json",
        help=(
            "Path to a Claude settings.json mounted read-only into the graph "
            "container. Pass --no-settings to rely solely on env-var credentials."
        ),
    )
    parser.add_argument(
        "--no-settings",
        action="store_true",
        help="Do not mount Claude settings; agents rely on environment credentials.",
    )
    parser.add_argument(
        "--no-auto-build",
        action="store_true",
        help="Fail instead of running `docker build` when the image is missing.",
    )
    parser.add_argument(
        "--readonly",
        type=Path,
        action="append",
        default=[],
        help=(
            "Project-relative or absolute path to mount read-only inside the "
            "graph container (may be repeated). The pipeline config is always "
            "added automatically."
        ),
    )
    return parser.parse_args(argv)


def _session_kwargs(state: PipelineStage) -> dict:
    """Common per-agent session kwargs (cwd, allowed_paths, model)."""
    allowed_paths = (
        state.config.resolved_scope(state.repo_path) if state.config else None
    )
    if allowed_paths is not None:
        if state.config is not None:
            allowed_paths.append((REFERENCE_ROOT / state.config.original_path).resolve())
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


def _validate_report(result: str, *, stage: str, heading: str) -> str:
    report = result.strip()
    if not report:
        raise ValueError(f"{stage} returned an empty report")
    if not report.startswith(heading):
        raise ValueError(f"{stage} report must start with {heading!r}")
    return report


def _record_report(state: PipelineStage, stage: str, report: str) -> None:
    state.reports.append((stage, report))
    logger.info("%s report:\n%s", stage, report)


def _write_generated_config(config_path: Path, result: str) -> PipelineConfig:
    text = result.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    raw = json.loads(text)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(raw, indent=2) + "\n")
    return PipelineConfig.load(config_path)


def _compile_reference(source: SourceFile, *, flags: str, output_file: Path) -> None:
    """Compile the baseline with all relative config paths rooted at /reference."""
    previous_cwd = Path.cwd()
    try:
        os.chdir(REFERENCE_ROOT.resolve())
        source.compile(kwds=flags, output_file=output_file)
    finally:
        os.chdir(previous_cwd)


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
    repo_path = (args.repo or Path.cwd()).resolve()
    config_path = _resolve_config_path(repo_path, args.config_path)

    if not args.no_docker and not os.environ.get("LASSI_GRAPH_IN_CONTAINER"):
        await _launch_graph_container(args, repo_path, config_path)
        return

    # Compile/exec invocations in lassi.core run subprocesses without a cwd
    # argument, so relative -I/source paths in the pipeline config resolve
    # against the host CWD. Mirror the container's /workspace = project root
    # convention by chdir'ing here.
    os.chdir(repo_path)

    logger.info("graph execution: %s", "container" if os.environ.get("LASSI_GRAPH_IN_CONTAINER") else "host (--no-docker)")
    if args.generate_config_only:
        await _generate_config_only(config_path, repo_path)
        return
    await _run_graph(args, config_path, repo_path)


def _container_path(host_path: Path, repo_path: Path) -> Path:
    try:
        return CONTAINER_WORKSPACE / host_path.relative_to(repo_path)
    except ValueError:
        return EXTERNAL_CONFIG_MOUNT


async def _generate_config_only(config_path: Path, repo_path: Path) -> None:
    if config_path.exists():
        PipelineConfig.load(config_path)
        return
    state = PipelineStage(config_path=config_path, repo_path=repo_path)
    result = await CONFIG_BUILDER_AGENT.dispatch_agent(
        **_session_kwargs(state),
        repo_path=repo_path,
    )
    _write_generated_config(config_path, result)
    _record_report(state, "config-builder", result.strip())


async def _launch_graph_container(
    args: argparse.Namespace,
    repo_path: Path,
    config_path: Path,
) -> None:
    if repo_path == Path("/"):
        raise SystemExit("refusing to mount the host root as the editable project")
    if not repo_path.is_dir():
        raise SystemExit(f"project directory does not exist: {repo_path}")

    settings_path: Path | None = None
    if not args.no_settings:
        settings_path = args.settings.expanduser().resolve()
        if not settings_path.is_file():
            raise SystemExit(
                f"Claude settings not found at {settings_path}; pass --no-settings "
                "or --settings PATH to override"
            )

    try:
        config_path.relative_to(repo_path)
        config_is_external = False
    except ValueError:
        config_is_external = True
    if config_is_external and not config_path.is_file():
        raise SystemExit(f"external config does not exist: {config_path}")

    extra_overlays = [
        (path if path.is_absolute() else repo_path / path).resolve()
        for path in args.readonly
    ]
    for path in extra_overlays:
        if not path.exists():
            raise SystemExit(f"read-only overlay does not exist: {path}")

    common = dict(
        project_dir=repo_path,
        image=args.image,
        settings_path=settings_path,
        repo_root=Path(__file__).resolve().parent.parent,
        auto_build=not args.no_auto_build,
        external_config=config_path if config_is_external else None,
    )

    # A generated config cannot be overlaid read-only in a running container.
    # Generate it in a short bootstrap container, then restart with final mounts.
    if not config_path.exists():
        with AgentContainer(**common, read_only_overlays=extra_overlays) as bootstrap:
            await bootstrap.exec_graph(
                [
                    str(CONTAINER_WORKSPACE),
                    str(_container_path(config_path, repo_path)),
                    "--generate-config-only",
                    "--no-settings",
                ]
            )

    config = PipelineConfig.load(config_path)
    original_path = (repo_path / config.original_path).resolve()
    try:
        original_path.relative_to(repo_path)
    except ValueError as exc:
        raise SystemExit(f"reference source escapes project: {original_path}") from exc
    if not original_path.is_file():
        raise SystemExit(f"reference source does not exist: {original_path}")

    overlays = [*extra_overlays]
    if not config_is_external:
        overlays.append(config_path)

    inner_args = [
        str(CONTAINER_WORKSPACE),
        str(_container_path(config_path, repo_path)),
    ]
    if args.no_profile:
        inner_args.append("--no-profile")
    inner_args.append("--no-settings")

    with tempfile.TemporaryDirectory(prefix="lassi-reference-") as temp_dir:
        reference_dir = Path(temp_dir) / "project"
        shutil.copytree(repo_path, reference_dir, symlinks=True)
        with AgentContainer(
            **common,
            reference_dir=reference_dir,
            read_only_overlays=overlays,
            reference_overlays=[config.original_path],
        ) as container:
            logger.info(
                "running graph in Docker (project=%s, reference snapshot=%s, ro overlays=%d)",
                repo_path, reference_dir, len(overlays) + 1,
            )
            await container.exec_graph(inner_args)


async def _run_graph(args: argparse.Namespace, config_path: Path, repo_path: Path) -> None:
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
            )
            _write_generated_config(cfg_path, ctx.state.llm_result)
            _record_report(ctx.state, "config-builder", ctx.state.llm_result.strip())
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
                folder_path=REFERENCE_ROOT,
                compiler_tool=CompilerTool(cfg.compiler),
            )
            (ctx.state.repo_path / BUILD_ROOT).mkdir(parents=True, exist_ok=True)
            _compile_reference(
                original,
                flags=cfg.correctness_flags,
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
        logger.info("building in-memory pipeline context")
        try:
            sample_golden = "\n".join(
                f"- args={a!r}" for a, _ in cfg.golden_outputs[:5]
            )
            ctx.state.context_message = (
                "# Pipeline Context\n\n"
                "This message is the seed instruction for the planner-coder chain.\n"
                "The planner inspects the source and produces one actionable plan.\n\n"
                "## Repository\n"
                f"- root: {ctx.state.repo_path}\n"
                f"- config: {ctx.state.config_path}\n\n"
                "## Target source\n"
                f"- reference (read-only): {REFERENCE_ROOT / cfg.original_path}\n"
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
            return "ok"
        except Exception as exc:
            ctx.state.error = f"context bootstrap failed: {exc}"
            return "fail"

    @g.step
    async def plan_refactor(ctx: StepContext[PipelineStage, None, object]) -> Ok | Fail:
        if not ctx.state.context_message:
            ctx.state.error = "plan step has no context message"
            return "fail"
        notes = ctx.state.plan_feedback or ""
        if notes:
            logger.info(
                "re-planning (round %d/%d) with feedback:\n%s",
                ctx.state.planner_iterations,
                ctx.state.max_planner_iterations,
                notes,
            )
        logger.info("dispatching planner with in-memory context")
        try:
            ctx.state.llm_result = await PLANNER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                context_message=ctx.state.context_message,
                notes=notes,
            )
            ctx.state.plan_message = _validate_report(
                ctx.state.llm_result,
                stage="planner",
                heading="# Plan",
            )
            _record_report(ctx.state, "planner", ctx.state.plan_message)
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
        if not ctx.state.plan_message:
            ctx.state.error = "coder step has no planner message"
            return "fail"
        original_full = REFERENCE_ROOT / cfg.original_path
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
            "dispatching coder against candidate %s with planner message",
            optimized_full,
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
                plan_message=ctx.state.plan_message,
                target_file=cfg.optimized_path,
                reference_file=REFERENCE_ROOT / cfg.original_path,
                notes=notes,
            )

            ctx.state.coder_report = _validate_report(
                ctx.state.llm_result,
                stage="coder",
                heading="# Changes",
            )
            _record_report(ctx.state, "coder", ctx.state.coder_report)
            if not optimized_full.exists():
                raise FileNotFoundError(f"coder removed {optimized_full}")
            if optimized_full.read_bytes() == candidate_before:
                # An unchanged candidate means the coder found no actionable
                # repair or implementation for the current plan.
                ctx.state.plan_feedback = (
                    f"Coder did not modify {cfg.optimized_path}. The current plan "
                    f"appears unactionable to the coder.\n"
                    f"Coder report:\n{ctx.state.coder_report}"
                )
                logger.warning("coder gave up; escalating to planner")
                return "giveup"

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
            _compile_reference(
                ctx.state.original,
                flags=cfg.correctness_flags,
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
            _compile_reference(
                ctx.state.original,
                flags=cfg.performance_flags,
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
        reports = "\n".join(f"    {i}. {stage}" for i, (stage, _) in enumerate(ctx.state.reports))
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
            + f"  message reports ({len(ctx.state.reports)}):\n{reports}\n"
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
