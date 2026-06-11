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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, stdev
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
from lassi.core.source_file import SourceFile
from lassi.profiling.profiler import Timer

class _ColoredFormatter(logging.Formatter):
    """Render compact, categorized graph logs with visible phase boundaries."""

    RESET = "\x1b[0m"
    CATEGORY_COLORS = {
        "pipeline": "\x1b[1;37m",   # bold white
        "docker": "\x1b[36m",       # cyan
        "build": "\x1b[34m",        # blue
        "verify": "\x1b[32m",       # green
        "agent": "\x1b[35m",        # magenta
        "benchmark": "\x1b[33m",    # yellow
    }
    LEVEL_COLORS = {
        "WARNING": "\x1b[1;33m",
        "ERROR": "\x1b[1;31m",
        "CRITICAL": "\x1b[1;31m",
    }
    LOGGER_CATEGORIES = {
        "graph.container_pool": "docker",
        "lassi.core.compiler": "build",
        "lassi.core.executer": "benchmark",
        "agents": "agent",
        "claude_agent_sdk": "agent",
    }

    def _category(self, record: logging.LogRecord) -> str:
        explicit = getattr(record, "category", None)
        if explicit:
            return explicit
        for prefix, category in self.LOGGER_CATEGORIES.items():
            if record.name.startswith(prefix):
                return category
        return "pipeline"

    def format(self, record: logging.LogRecord) -> str:
        category = self._category(record)
        color = self.LEVEL_COLORS.get(
            record.levelname,
            self.CATEGORY_COLORS.get(category, ""),
        )
        message = record.getMessage()
        if getattr(record, "section", False):
            title = f" {message.upper()} "
            width = max(20, 78 - len(title))
            left = width // 2
            right = width - left
            return f"\n{color}{'=' * left}{title}{'=' * right}{self.RESET}"
        label = record.levelname if record.levelno >= logging.WARNING else category.upper()
        return f"{color}[{label:<9}]{self.RESET} {message}"


_handler = logging.StreamHandler()
_handler.setFormatter(_ColoredFormatter("%(levelname)s:%(name)s:%(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[_handler], force=True)
logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "graph_code_test.json"
BUILD_ROOT = Path(os.environ.get("LASSI_BUILD_ROOT", ".verify/refactoring"))
REFERENCE_ROOT = Path(os.environ.get("LASSI_REFERENCE_ROOT", "."))
CLAUDE_MODEL = "claude-opus-4-7"


def _log(category: str, message: str, *args) -> None:
    logger.info(message, *args, extra={"category": category})


def _section(title: str, *, category: str = "pipeline") -> None:
    logger.info(title, extra={"category": category, "section": True})

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


DEFAULT_SAFETY_FLAGS = "-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1"
DEFAULT_CBMC_ARGS = "--bounds-check --pointer-check --signed-overflow-check --unwind 8"


@dataclass
class TestCase:
    """One concrete execution of a built binary.

    `stdout` and `stderr` are *expected* outputs; either or both may be None,
    in which case that stream is not checked (useful e.g. when DUMP_ARRAYS
    writes to stderr and stdout is empty/uninteresting).
    """
    args: str
    stdout: str | None = None
    stderr: str | None = None


@dataclass
class CorrectnessGroup:
    """One (compile_args, tests) bundle.

    Every step that today uses a single correctness build runs once per group:
    compile the source with `compile_args`, then execute every `golden`
    (validated byte-exact) and every `differential` (compared
    original-vs-optimized at runtime).
    """
    compile_args: str
    golden: list[TestCase] = field(default_factory=list)
    differential: list[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    original_path: Path
    optimized_path: Path
    compiler: Compiler
    correctness_groups: list[CorrectnessGroup]
    performance_flags: str
    benchmark_args: str
    benchmark_runs: int
    target_speedup: float
    scope: list[Path] | None  # None = unrestricted
    safety_mode: Literal["asan", "cbmc", "off"] = "asan"
    safety_flags: str = DEFAULT_SAFETY_FLAGS
    cbmc_args: str = DEFAULT_CBMC_ARGS
    # Subset of correctness_groups indices to run under ASAN. `None` = all groups
    # (default). Use to cap safety cost on configs that contain large groups —
    # UB usually surfaces at small sizes, so sanitizing only the MINI group is
    # often sufficient and orders of magnitude faster.
    safety_groups: list[int] | None = None

    @classmethod
    def load(cls, path: Path) -> PipelineConfig:
        raw = json.loads(path.read_text())
        sources = raw["sources"]
        flags = raw["flags"]
        args = raw["arguments"]

        # Hard cutover: refuse the old singleton-build shape so a forgotten
        # config doesn't silently lose coverage. See migration note in the
        # config-builder agent spec for the new shape.
        legacy_signals = []
        if "correctness" in flags:
            legacy_signals.append("flags.correctness (use arguments.correctness[*].compile_args)")
        if "golden" in args and isinstance(args["golden"], list):
            legacy_signals.append("arguments.golden (move into arguments.correctness[*].golden)")
        if "differential" in args and isinstance(args.get("differential"), list):
            legacy_signals.append("arguments.differential (move into arguments.correctness[*].differential)")
        if legacy_signals:
            raise ValueError(
                "config uses the old single-build schema; restructure into "
                "arguments.correctness = [{compile_args, golden, differential}, ...]. "
                "Stale keys: " + "; ".join(legacy_signals)
            )

        raw_groups = args.get("correctness")
        if not isinstance(raw_groups, list) or not raw_groups:
            raise ValueError(
                "arguments.correctness must be a non-empty list of "
                "{compile_args, golden, differential} groups"
            )
        groups: list[CorrectnessGroup] = []
        for i, g in enumerate(raw_groups):
            if "compile_args" not in g:
                raise ValueError(f"arguments.correctness[{i}].compile_args is required")
            tests = [
                TestCase(
                    args=t.get("args", ""),
                    stdout=t.get("stdout"),
                    stderr=t.get("stderr"),
                )
                for t in g.get("golden", [])
            ]
            differential = list(g.get("differential", []))
            groups.append(CorrectnessGroup(
                compile_args=g["compile_args"],
                golden=tests,
                differential=differential,
            ))

        original_path = _project_relative_path(sources["original"], "sources.original")
        optimized_path = _project_relative_path(sources["optimized"], "sources.optimized")
        if original_path == optimized_path:
            raise ValueError("sources.original and sources.optimized must be different paths")
        scope = (
            [_project_relative_path(p, "scope entry") for p in raw["scope"]]
            if "scope" in raw
            else None
        )
        safety = raw.get("safety", {}) or {}
        safety_mode = safety.get("mode", "asan")
        if safety_mode not in ("asan", "cbmc", "off"):
            raise ValueError(f"safety.mode must be asan|cbmc|off, got {safety_mode!r}")
        safety_groups_raw = safety.get("groups")
        safety_groups: list[int] | None
        if safety_groups_raw is None:
            safety_groups = None
        else:
            if not isinstance(safety_groups_raw, list) or not all(
                isinstance(i, int) for i in safety_groups_raw
            ):
                raise ValueError("safety.groups must be a list of integer indices")
            n = len(groups)
            bad = [i for i in safety_groups_raw if i < 0 or i >= n]
            if bad:
                raise ValueError(
                    f"safety.groups indices {bad} out of range for {n} correctness group(s)"
                )
            safety_groups = list(dict.fromkeys(safety_groups_raw))  # dedupe, preserve order
        return cls(
            original_path=original_path,
            optimized_path=optimized_path,
            compiler=Compiler(raw["compiler"]),
            correctness_groups=groups,
            performance_flags=flags["performance"],
            benchmark_args=args["benchmark"],
            benchmark_runs=int(args.get("benchmark_runs", 5)),
            target_speedup=float(args.get("target_speedup", 0.0)),
            scope=scope,
            safety_mode=safety_mode,
            safety_flags=safety.get("asan_flags", DEFAULT_SAFETY_FLAGS),
            cbmc_args=safety.get("cbmc_args", DEFAULT_CBMC_ARGS),
            safety_groups=safety_groups,
        )

    def selected_safety_groups(self) -> list[tuple[int, CorrectnessGroup]]:
        """Return (index, group) pairs that should be sanitized."""
        if self.safety_groups is None:
            return list(enumerate(self.correctness_groups))
        return [(i, self.correctness_groups[i]) for i in self.safety_groups]

    def total_goldens(self) -> int:
        return sum(len(g.golden) for g in self.correctness_groups)

    def total_differentials(self) -> int:
        return sum(len(g.differential) for g in self.correctness_groups)

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
    attempts: list[AttemptRecord] = field(default_factory=list)
    error: str | None = None


@dataclass
class BenchmarkStats:
    samples: list[float]
    mean: float
    median: float
    stdev: float
    minimum: float
    maximum: float
    cv_pct: float


@dataclass
class AttemptRecord:
    planner_round: int
    coder_round: int
    strategy: str
    outcome: str = "pending"
    feedback: str = ""
    original_stats: BenchmarkStats | None = None
    optimized_stats: BenchmarkStats | None = None
    speedup_pct: float | None = None


def _project_relative_path(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a project-relative path: {value!r}")
    return path


def _resolve_config_path(repo_path: Path, config_path: Path) -> Path:
    if config_path.is_absolute():
        return config_path.resolve()
    return (repo_path / config_path).resolve()


_CONFIG_NAME_SUFFIXES = (
    "_graph_config",
    "_graph_code_test",
    "_pipeline",
    "_config",
)


def _resolve_target_path(target: Path | None, repo_path: Path) -> Path | None:
    """Validate --target and return it as a repo-relative Path, or None if unset."""
    if target is None:
        return None
    candidate = target if target.is_absolute() else (repo_path / target)
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise SystemExit(f"--target does not exist or is not a file: {candidate}")
    try:
        rel = candidate.relative_to(repo_path.resolve())
    except ValueError as exc:
        raise SystemExit(
            f"--target {candidate} is outside the project root {repo_path}"
        ) from exc
    return rel


def _target_hint_from_config_path(config_path: Path) -> str | None:
    """Derive a target-kernel hint from a config filename (e.g. lu_graph_config.json -> 'lu')."""
    stem = config_path.stem
    if not stem:
        return None
    lowered = stem.lower()
    for suffix in _CONFIG_NAME_SUFFIXES:
        if lowered.endswith(suffix) and len(stem) > len(suffix):
            stem = stem[: -len(suffix)]
            break
    stem = stem.strip("._-")
    if not stem or stem.lower() in {"graph_code_test", "pipeline", "config"}:
        return None
    return stem


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
        "--target",
        type=Path,
        default=None,
        help=(
            "Path to the source file the config-builder should target as "
            "`sources.original` (absolute or repo-relative). Required when "
            "generating a config for a multi-kernel repo; ignored when the "
            "config already exists."
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
        help="Use an existing image instead of refreshing it with `docker build`.",
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
    """Common per-agent session kwargs (cwd, allowed_paths, model).

    Also widens the scope to cover the LASSI artifact dir so the profiling
    skills (gprof/perf/hyperfine/roofline wrappers) can write JSON outputs
    the agent then reads back.
    """
    allowed_paths = (
        state.config.resolved_scope(state.repo_path) if state.config else None
    )
    if allowed_paths is not None:
        if state.config is not None:
            allowed_paths.append((REFERENCE_ROOT / state.config.original_path).resolve())
        artifact_dir = Path(
            os.environ.get("LASSI_ARTIFACT_DIR", state.repo_path / "LASSI")
        )
        allowed_paths.append(artifact_dir.resolve())
    return {
        "cwd": state.repo_path,
        "allowed_paths": allowed_paths,
        "model": CLAUDE_MODEL,
    }


def _benchmark_pair(
    original: SourceFile,
    optimized: SourceFile,
    *,
    args: str,
    runs: int,
) -> tuple[list[float], list[float]]:
    """Benchmark both variants in a balanced, interleaved order.

    Running every baseline sample before every candidate sample systematically
    exposes the candidate to later-run thermal and scheduler conditions. Use
    an even sample count and alternate AB/BA ordering to balance that effect.
    """
    if runs < 1:
        raise ValueError(f"benchmark_runs must be at least 1, got {runs}")
    balanced_runs = runs if runs % 2 == 0 else runs + 1
    original_latencies: list[float] = []
    optimized_latencies: list[float] = []
    for i in range(balanced_runs):
        ordered = (
            ((original, original_latencies), (optimized, optimized_latencies))
            if i % 2 == 0
            else ((optimized, optimized_latencies), (original, original_latencies))
        )
        for source, latencies in ordered:
            report = source.execute(args=args, profiler=Timer())
            latencies.append(report.latency)
    return original_latencies, optimized_latencies


def _benchmark_stats(samples: list[float]) -> BenchmarkStats:
    if not samples:
        raise ValueError("cannot summarize an empty benchmark sample set")
    sample_mean = mean(samples)
    sample_stdev = stdev(samples) if len(samples) > 1 else 0.0
    return BenchmarkStats(
        samples=list(samples),
        mean=sample_mean,
        median=median(samples),
        stdev=sample_stdev,
        minimum=min(samples),
        maximum=max(samples),
        cv_pct=(sample_stdev / sample_mean * 100.0) if sample_mean else 0.0,
    )


def _format_benchmark_stats(label: str, stats: BenchmarkStats) -> str:
    samples = ", ".join(f"{sample:.6f}" for sample in stats.samples)
    return (
        f"{label}: mean={stats.mean:.6f}s median={stats.median:.6f}s "
        f"stdev={stats.stdev:.6f}s cv={stats.cv_pct:.2f}% "
        f"min={stats.minimum:.6f}s max={stats.maximum:.6f}s "
        f"samples=[{samples}]"
    )


def _extract_strategy(report: str) -> str:
    in_strategy = False
    for line in report.splitlines():
        stripped = line.strip()
        if stripped == "## Strategy applied":
            in_strategy = True
            continue
        if in_strategy and stripped.startswith("- "):
            return stripped[2:].strip()
        if in_strategy and stripped.startswith("## "):
            break
    return "(strategy not reported)"


def _latest_attempt(state: PipelineStage) -> AttemptRecord | None:
    return state.attempts[-1] if state.attempts else None


def _compact_text(text: str, *, limit: int = 1200) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _attempt_history_summary(state: PipelineStage) -> str:
    if not state.attempts:
        return "- none"
    lines = []
    for i, attempt in enumerate(state.attempts, start=1):
        speedup = (
            f", mean speedup={attempt.speedup_pct:+.2f}%"
            if attempt.speedup_pct is not None
            else ""
        )
        lines.append(
            f"- attempt {i} (plan {attempt.planner_round}, coder {attempt.coder_round}): "
            f"{attempt.strategy}; outcome={attempt.outcome}{speedup}"
        )
        if attempt.feedback:
            lines.append(f"  feedback: {_compact_text(attempt.feedback)}")
    return "\n".join(lines)


def _task_context_summary(state: PipelineStage, *, role: str) -> str:
    cfg = state.config
    assert cfg is not None
    latest_metrics = ""
    latest = _latest_attempt(state)
    if latest and latest.original_stats and latest.optimized_stats:
        latest_metrics = (
            "\nLatest benchmark statistics:\n"
            f"- {_format_benchmark_stats('original', latest.original_stats)}\n"
            f"- {_format_benchmark_stats('optimized', latest.optimized_stats)}"
        )
    return (
        f"# Context Summary for {role}\n"
        f"- target: {cfg.optimized_path}\n"
        f"- reference: {REFERENCE_ROOT / cfg.original_path}\n"
        f"- compiler: {cfg.compiler.value}\n"
        f"- performance flags: {cfg.performance_flags}\n"
        f"- acceptance gate: mean speedup strictly greater than {cfg.target_speedup:.2f}%\n"
        f"- planner round: {state.planner_iterations}; coder round: {state.coder_iterations}\n"
        f"- latest feedback: "
        f"{_compact_text(state.code_feedback or state.plan_feedback or '(none)')}\n"
        "Attempt history:\n"
        f"{_attempt_history_summary(state)}"
        f"{latest_metrics}"
    )


def _write_benchmark_history(state: PipelineStage) -> Path:
    path = state.repo_path / BUILD_ROOT / "benchmark_history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "acceptance_metric": "mean_speedup_pct",
        "target_speedup_pct": state.config.target_speedup if state.config else None,
        "attempts": [asdict(attempt) for attempt in state.attempts],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


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
    """Strip preamble around a Markdown report.

    Empty replies are fatal (the agent produced nothing actionable). If the
    expected heading appears anywhere (start of file or after a newline), the
    returned report begins with that heading line — any preamble like
    'Here are the changes:' is dropped. If the heading is absent the original
    stripped reply is returned and a warning is logged; we no longer abort
    the pipeline over a missing heading.
    """
    report = result.strip()
    if not report:
        raise ValueError(f"{stage} returned an empty report")
    if not report.startswith(heading):
        marker = f"\n{heading}"
        pos = report.find(marker)
        if pos != -1:
            report = report[pos + 1 :].strip()
        else:
            logger.warning(
                "%s report did not include expected heading %r; using the raw reply",
                stage, heading,
            )
    lines = report.splitlines()
    fence_count = sum(1 for line in lines if line.strip().startswith("```"))
    if lines and lines[-1].strip() == "```" and fence_count % 2 == 1:
        report = "\n".join(lines[:-1]).rstrip()
    return report


def _record_report(state: PipelineStage, stage: str, report: str) -> None:
    state.reports.append((stage, report))
    _log("agent", "%s report:\n%s", stage, report)


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
    _strip_workspace_prefix(raw)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(raw, indent=2) + "\n")
    return PipelineConfig.load(config_path)


def _strip_workspace_prefix(raw: dict) -> None:
    """Defensively rewrite agent-emitted /workspace/... paths to repo-relative."""
    def _fix(value: str) -> str:
        if not isinstance(value, str):
            return value
        prefix = str(CONTAINER_WORKSPACE).rstrip("/") + "/"
        if value.startswith(prefix):
            return value[len(prefix):]
        if value == str(CONTAINER_WORKSPACE):
            return "."
        return value

    sources = raw.get("sources")
    if isinstance(sources, dict):
        for key in ("original", "optimized"):
            if key in sources:
                sources[key] = _fix(sources[key])
    scope = raw.get("scope")
    if isinstance(scope, list):
        raw["scope"] = [_fix(p) for p in scope]


def _compile_reference(source: SourceFile, *, flags: str, output_file: Path) -> None:
    """Compile the baseline with all relative config paths rooted at /reference."""
    previous_cwd = Path.cwd()
    try:
        os.chdir(REFERENCE_ROOT.resolve())
        source.compile(kwds=flags, output_file=output_file)
    finally:
        os.chdir(previous_cwd)


def _gcovr_summary(root: Path, *, filter_source: Path | None = None) -> str | None:
    # The pipeline compiles with clang, so coverage notes (.gcno/.gcda) are
    # in LLVM's format. gcovr's default `gcov` is GNU's and cannot parse
    # them ("version '408*', prefer 'B33*'"). `llvm-cov gcov` is the clang
    # shim that emits GNU-compatible output from the same notes.
    #
    # `filter_source` restricts gcovr to a single source file's coverage.
    # Without it, gcovr scans every .gcno/.gcda it can find — which trips
    # over multi-build (per-group) coverage of the same source file.
    cmd = [
        "gcovr",
        "--root", str(root),
        "--gcov-executable", "llvm-cov gcov",
        "--print-summary",
    ]
    if filter_source is not None:
        cmd.extend(["--filter", str(filter_source.resolve())])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
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


def _format_stream_mismatch(stream: str, expected: str, actual: str) -> str:
    return (
        f"      {stream} mismatch:\n"
        f"        expected: {expected!r}\n"
        f"        got:      {actual!r}"
    )


def _run_test_case(
    executable: Path, case: TestCase, *, env: dict | None = None, timeout_s: int = 300,
) -> tuple[bool, str]:
    """Run `executable` with `case.args`, validate stdout/stderr/returncode.

    `case.stdout` and `case.stderr` are optional: a None means "don't check".
    Returns (ok, diagnostic). Diagnostic is empty on success.
    """
    cmd = [str(executable.resolve()), *case.args.split()] if case.args else [str(executable.resolve())]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env)
    except subprocess.TimeoutExpired as exc:
        return False, f"  args={case.args!r}: timeout ({exc.timeout}s)"
    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"      nonzero exit: {proc.returncode}")
    if case.stdout is not None and proc.stdout != case.stdout:
        failures.append(_format_stream_mismatch("stdout", case.stdout, proc.stdout))
    if case.stderr is not None and proc.stderr != case.stderr:
        failures.append(_format_stream_mismatch("stderr", case.stderr, proc.stderr))
    if failures:
        return False, f"  args={case.args!r}:\n" + "\n".join(failures)
    return True, ""


def _compile_group(
    source: SourceFile, *, compile_args: str, output_file: Path, in_reference_root: bool,
) -> tuple[bool, str]:
    """Compile `source` once with `compile_args`. Return (ok, error_message)."""
    try:
        if in_reference_root:
            _compile_reference(source, flags=compile_args, output_file=output_file)
        else:
            source.compile(kwds=compile_args, output_file=output_file)
        return True, ""
    except Exception as exc:
        return False, f"compile failed with `{compile_args}`: {exc}"


ASAN_MARKERS = (
    "AddressSanitizer:",
    "UndefinedBehaviorSanitizer:",
    "LeakSanitizer:",
    "runtime error:",
    "SUMMARY: AddressSanitizer",
    "SUMMARY: UndefinedBehaviorSanitizer",
)


def _asan_diagnostic(args: str, stderr: str, returncode: int) -> str | None:
    """Return a one-block diagnostic string if stderr looks like a sanitizer hit."""
    if returncode == 0 and not any(m in stderr for m in ASAN_MARKERS):
        return None
    head = stderr.strip().splitlines()
    snippet = "\n      ".join(head[:40]) if head else "(empty stderr)"
    return (
        f"  args={args!r} (exit={returncode}):\n"
        f"      {snippet}"
    )


_ASAN_ENV = {
    "ASAN_OPTIONS": "halt_on_error=1:detect_leaks=1:abort_on_error=0:strict_string_checks=1",
    "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1",
}


def _run_asan_over_inputs(executable: Path, input_args: list[str]) -> list[str]:
    """Run `executable` once per input under ASAN env. Return per-input diagnostics."""
    env = {**os.environ, **_ASAN_ENV}
    failures: list[str] = []
    for args in input_args:
        cmd = [str(executable.resolve()), *args.split()] if args else [str(executable.resolve())]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
        except subprocess.TimeoutExpired as exc:
            failures.append(f"  args={args!r}: timeout ({exc.timeout}s)")
            continue
        diag = _asan_diagnostic(args, proc.stderr, proc.returncode)
        if diag is not None:
            failures.append(diag)
    return failures


def _run_cbmc_check(source_path: Path, *, cbmc_args: str) -> tuple[bool, str]:
    """Invoke cbmc on the C source directly. Return (ok, diagnostic)."""
    if shutil.which("cbmc") is None:
        return False, "cbmc binary not found on PATH"
    cmd = ["cbmc", str(source_path), *cbmc_args.split()]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired as exc:
        return False, f"cbmc timed out after {exc.timeout}s"
    output = (proc.stdout or "") + (proc.stderr or "")
    if "VERIFICATION SUCCESSFUL" in output:
        return True, ""
    if "VERIFICATION FAILED" in output:
        # Keep the head of the report; trailing trace can be very long.
        snippet = "\n".join(output.strip().splitlines()[-60:])
        return False, f"cbmc reported VERIFICATION FAILED (exit={proc.returncode}):\n{snippet}"
    snippet = "\n".join(output.strip().splitlines()[-40:])
    return False, f"cbmc exited {proc.returncode} without a verdict; tail:\n{snippet}"


def _run_differential_cases(
    original_exe: Path, optimized_exe: Path, cases: list[str], *, timeout_s: int = 60,
) -> list[str]:
    """Run both binaries on each input arg-string; return per-case mismatch lines (empty = all match).

    Compares returncode, stdout, and stderr. PolyBench-style kernels write the
    deterministic array dump to stderr, so checking both streams is required.
    """
    mismatches: list[str] = []
    for args in cases:
        argv = args.split() if args else []
        cmd_o = [str(original_exe.resolve()), *argv]
        cmd_c = [str(optimized_exe.resolve()), *argv]
        try:
            proc_o = subprocess.run(cmd_o, capture_output=True, text=True, timeout=timeout_s)
            proc_c = subprocess.run(cmd_c, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            mismatches.append(f"  args={args!r}: timeout ({exc.timeout}s)")
            continue
        per_input: list[str] = []
        if proc_o.returncode != proc_c.returncode:
            per_input.append(
                f"      returncode: original={proc_o.returncode} optimized={proc_c.returncode}"
            )
        if proc_o.stdout != proc_c.stdout:
            per_input.append(
                f"      stdout differs (orig={proc_o.stdout!r} vs opt={proc_c.stdout!r})"
            )
        if proc_o.stderr != proc_c.stderr:
            per_input.append(
                f"      stderr differs (orig={proc_o.stderr!r} vs opt={proc_c.stderr!r})"
            )
        if per_input:
            mismatches.append(f"  args={args!r}:\n" + "\n".join(per_input))
    return mismatches


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
        target_path = _resolve_target_path(args.target, repo_path)
        await _generate_config_only(config_path, repo_path, target_path=target_path)
        return
    await _run_graph(args, config_path, repo_path)


def _container_path(host_path: Path, repo_path: Path) -> Path:
    try:
        return CONTAINER_WORKSPACE / host_path.relative_to(repo_path)
    except ValueError:
        return EXTERNAL_CONFIG_MOUNT


async def _generate_config_only(
    config_path: Path,
    repo_path: Path,
    *,
    target_path: Path | None = None,
) -> None:
    if config_path.exists():
        PipelineConfig.load(config_path)
        return
    state = PipelineStage(config_path=config_path, repo_path=repo_path)
    try:
        result = await CONFIG_BUILDER_AGENT.dispatch_agent(
            **_session_kwargs(state),
            repo_path=repo_path,
            target_path=target_path,
            target_hint=(
                None if target_path is not None
                else _target_hint_from_config_path(config_path)
            ),
        )
        _write_generated_config(config_path, result)
        _record_report(state, "config-builder", result.strip())
    finally:
        await CONFIG_BUILDER_AGENT.close()


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
        bootstrap_argv = [
            str(CONTAINER_WORKSPACE),
            str(_container_path(config_path, repo_path)),
            "--generate-config-only",
            "--no-settings",
        ]
        host_target = _resolve_target_path(args.target, repo_path)
        if host_target is not None:
            bootstrap_argv += [
                "--target",
                str(CONTAINER_WORKSPACE / host_target),
            ]
        with AgentContainer(**common, read_only_overlays=extra_overlays) as bootstrap:
            await bootstrap.exec_graph(bootstrap_argv)

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
        _section("Setup")
        cfg_path = ctx.state.config_path
        if not cfg_path.exists():
            logger.info("config %s not found; will ask agent to generate it", cfg_path)
            return "missing"
        try:
            ctx.state.config = PipelineConfig.load(cfg_path)
            cfg = ctx.state.config
            logger.info(
                "loaded config from %s: compiler=%s sources=(%s -> %s) "
                "groups=%d goldens=%d differentials=%d target_speedup=%.2f%%",
                cfg_path,
                cfg.compiler.value,
                cfg.original_path,
                cfg.optimized_path,
                len(cfg.correctness_groups),
                cfg.total_goldens(),
                cfg.total_differentials(),
                cfg.target_speedup,
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
        target_path = _resolve_target_path(getattr(args, "target", None), repo)
        try:
            ctx.state.llm_result = await CONFIG_BUILDER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                repo_path=repo,
                target_path=target_path,
                target_hint=(
                    None if target_path is not None
                    else _target_hint_from_config_path(cfg_path)
                ),
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
        _section("Reference validation", category="verify")
        assert ctx.state.config is not None
        cfg = ctx.state.config
        n_groups = len(cfg.correctness_groups)
        _log(
            "verify",
            "sanity-checking original (%s) across %d group(s), %d golden case(s) total",
            cfg.original_path, n_groups, cfg.total_goldens(),
        )
        original = SourceFile(
            file_name=cfg.original_path,
            folder_path=REFERENCE_ROOT,
            compiler_tool=CompilerTool(cfg.compiler),
        )
        (ctx.state.repo_path / BUILD_ROOT).mkdir(parents=True, exist_ok=True)
        ctx.state.original = original

        group_failures: list[str] = []
        for i, group in enumerate(cfg.correctness_groups):
            out = ctx.state.repo_path / BUILD_ROOT / f"original_sanity_g{i}"
            ok, err = _compile_group(
                original, compile_args=group.compile_args, output_file=out, in_reference_root=True,
            )
            if not ok:
                group_failures.append(
                    f"[group {i}] ORIGINAL FAILED TO COMPILE with `{group.compile_args}`:\n    {err}"
                )
                continue
            case_failures: list[str] = []
            for case in group.golden:
                case_ok, diag = _run_test_case(original.executable, case)
                if not case_ok:
                    case_failures.append(diag)
            if case_failures:
                group_failures.append(
                    f"[group {i}] {len(case_failures)}/{len(group.golden)} golden case(s) failed "
                    f"(compile_args=`{group.compile_args}`):\n" + "\n".join(case_failures)
                )

        if group_failures:
            ctx.state.error = (
                "ORIGINAL CODE FAILS ITS OWN UNIT TESTS.\n"
                f"Check {ctx.state.config_path}.\n"
                + "\n".join(group_failures)
            )
            return "fail"

        _log(
            "verify",
            "sanity check passed: %d/%d golden(s) across %d group(s)",
            cfg.total_goldens(), cfg.total_goldens(), n_groups,
        )
        return "ok"

    @g.step
    async def safety_check_original(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Skip | Fail:
        _section("Reference safety", category="verify")
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        cfg = ctx.state.config
        if cfg.safety_mode == "off":
            _log("verify", "safety mode = off; skipping baseline safety check")
            return "skip"
        _log(
            "verify",
            "safety_check_original: mode=%s, %d group(s)",
            cfg.safety_mode, len(cfg.correctness_groups),
        )

        if cfg.safety_mode == "cbmc":
            # CBMC reads the source directly; one invocation regardless of groups.
            ok, diag = _run_cbmc_check(
                (REFERENCE_ROOT / cfg.original_path).resolve(),
                cbmc_args=cfg.cbmc_args,
            )
            if not ok:
                ctx.state.error = (
                    f"ORIGINAL CODE FAILS SAFETY CHECK (CBMC).\n"
                    f"The reference {cfg.original_path} is unsafe; refusing to optimize.\n"
                    f"{diag}"
                )
                return "fail"
            _log("verify", "safety check (original, CBMC) passed")
            return "ok"

        # ASAN path: build with `compile_args + safety_flags` for each
        # selected group, run every golden + differential input.
        selected = cfg.selected_safety_groups()
        if not selected:
            _log("verify", "safety.groups is empty; skipping baseline ASAN check")
            return "skip"
        group_failures: list[str] = []
        for i, group in selected:
            out = ctx.state.repo_path / BUILD_ROOT / f"original_safety_g{i}"
            combined = f"{group.compile_args} {cfg.safety_flags}"
            ok, err = _compile_group(
                ctx.state.original, compile_args=combined, output_file=out, in_reference_root=True,
            )
            if not ok:
                group_failures.append(f"[group {i}] sanitizer build failed: {err}")
                continue
            inputs = [c.args for c in group.golden] + list(group.differential)
            asan_failures = _run_asan_over_inputs(ctx.state.original.executable, inputs)
            if asan_failures:
                group_failures.append(
                    f"[group {i}] sanitizer reported {len(asan_failures)} issue(s) "
                    f"(compile_args=`{group.compile_args}`):\n" + "\n".join(asan_failures)
                )

        if group_failures:
            ctx.state.error = (
                "ORIGINAL CODE FAILS SAFETY CHECK (ASAN+UBSan).\n"
                f"The reference {cfg.original_path} is unsafe; refusing to optimize.\n"
                + "\n".join(group_failures)
            )
            return "fail"
        _log("verify", "safety check (original, ASAN) passed across %d group(s)", len(selected))
        return "ok"

    @g.step
    async def bootstrap_context(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Fail:
        assert ctx.state.config is not None
        cfg = ctx.state.config
        logger.info("building in-memory pipeline context")
        try:
            ctx.state.candidate_seeded = _ensure_candidate_seeded(
                REFERENCE_ROOT / cfg.original_path,
                ctx.state.repo_path / cfg.optimized_path,
                already_seeded=ctx.state.candidate_seeded,
            )
            group_lines: list[str] = []
            for i, group in enumerate(cfg.correctness_groups):
                sample_args = ", ".join(
                    repr(c.args) for c in group.golden[:3]
                ) or "(none)"
                group_lines.append(
                    f"- group {i}: compile_args=`{group.compile_args}`\n"
                    f"    goldens: {len(group.golden)} (sample args: {sample_args})\n"
                    f"    differentials: {len(group.differential)}"
                )
            groups_block = "\n".join(group_lines)

            if cfg.safety_mode == "asan":
                if cfg.safety_groups is None:
                    scope_desc = f"all {len(cfg.correctness_groups)} group(s)"
                else:
                    scope_desc = f"group(s) {cfg.safety_groups}"
                safety_line = (
                    f"- safety gate: ASAN+UBSan applied to {scope_desc} "
                    f"(flags appended: {cfg.safety_flags})\n"
                    "- The optimized variant must not trip AddressSanitizer, "
                    "UndefinedBehaviorSanitizer, or LeakSanitizer on any golden or "
                    "differential input in the sanitized groups.\n"
                )
            elif cfg.safety_mode == "cbmc":
                safety_line = (
                    f"- safety gate: CBMC ({cfg.cbmc_args})\n"
                    "- The optimized source must verify with CBMC.\n"
                )
            else:
                safety_line = "- safety gate: disabled (mode=off)\n"

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
                f"- performance flags: {cfg.performance_flags}\n\n"
                "## Workload\n"
                f"- benchmark args: {cfg.benchmark_args!r}\n"
                f"- benchmark runs: {cfg.benchmark_runs}\n"
                f"- target speedup (strict, %): > {cfg.target_speedup:.2f}\n\n"
                "## Correctness regimes\n"
                f"Every test step compiles the source once per group with that group's "
                f"`compile_args`, then runs that group's goldens (stdout+stderr+returncode "
                f"byte-exact) and differentials (compared original-vs-optimized).\n"
                f"{groups_block}\n\n"
                "## Safety gate\n"
                f"{safety_line}"
            )
            return "ok"
        except Exception as exc:
            ctx.state.error = f"context bootstrap failed: {exc}"
            return "fail"

    @g.step
    async def plan_refactor(ctx: StepContext[PipelineStage, None, object]) -> Ok | Fail:
        _section("Planning", category="agent")
        if not ctx.state.context_message:
            ctx.state.error = "plan step has no context message"
            return "fail"
        notes = ctx.state.plan_feedback or ""
        if notes:
            _log(
                "agent",
                "re-planning (round %d/%d) with feedback:\n%s",
                ctx.state.planner_iterations,
                ctx.state.max_planner_iterations,
                notes,
            )
        _log("agent", "dispatching planner with in-memory context")
        try:
            # Every graph task starts a fresh agent session. The explicit
            # summary below is the only retry/re-plan context it should need.
            await PLANNER_AGENT.close()
            ctx.state.llm_result = await PLANNER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                context_message=ctx.state.context_message,
                context_summary=_task_context_summary(ctx.state, role="planner"),
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
        _section("Coding", category="agent")
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
            _log(
                "agent",
                "coder retry round %d/%d with feedback:\n%s",
                ctx.state.coder_iterations,
                ctx.state.max_coder_iterations,
                notes,
            )
        _log(
            "agent",
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

            await CODER_AGENT.close()
            ctx.state.llm_result = await CODER_AGENT.dispatch_agent(
                **_session_kwargs(ctx.state),
                plan_message=ctx.state.plan_message,
                target_file=cfg.optimized_path,
                reference_file=REFERENCE_ROOT / cfg.original_path,
                context_summary=_task_context_summary(ctx.state, role="coder"),
                notes=notes,
            )

            ctx.state.coder_report = _validate_report(
                ctx.state.llm_result,
                stage="coder",
                heading="# Changes",
            )
            _record_report(ctx.state, "coder", ctx.state.coder_report)
            ctx.state.attempts.append(
                AttemptRecord(
                    planner_round=ctx.state.planner_iterations,
                    coder_round=ctx.state.coder_iterations,
                    strategy=_extract_strategy(ctx.state.coder_report),
                )
            )
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
                attempt = _latest_attempt(ctx.state)
                if attempt is not None:
                    attempt.outcome = "no source change"
                    attempt.feedback = ctx.state.plan_feedback
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
        _section("Correctness", category="verify")
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        assert ctx.state.optimized is not None
        cfg = ctx.state.config
        n_groups = len(cfg.correctness_groups)
        _log(
            "verify",
            "test_refactor: running %d group(s) (%d goldens + %d differentials total)",
            n_groups, cfg.total_goldens(), cfg.total_differentials(),
        )

        # Only group 0 is built with --coverage. Reporting coverage across
        # multiple groups fails: different #ifdef regimes shift the line of
        # the same function, and gcovr can't reconcile them. Group 0 is the
        # representative regime (smallest by config-builder convention).
        # Stale .gcno/.gcda from any prior run poison the next gcovr report,
        # so wipe BUILD_ROOT (where --coverage actually writes them) too.
        build_dir = ctx.state.repo_path / BUILD_ROOT
        for d in (ctx.state.repo_path, build_dir):
            if d.is_dir():
                for stale in list(d.glob("*.gcno")) + list(d.glob("*.gcda")):
                    stale.unlink()

        group_failures: list[str] = []
        for i, group in enumerate(cfg.correctness_groups):
            opt_flags = f"{group.compile_args} --coverage" if i == 0 else group.compile_args
            orig_out = ctx.state.repo_path / BUILD_ROOT / f"original_correctness_g{i}"
            opt_out = ctx.state.repo_path / BUILD_ROOT / f"optimized_correctness_g{i}"
            ok_orig, err_orig = _compile_group(
                ctx.state.original, compile_args=group.compile_args,
                output_file=orig_out, in_reference_root=True,
            )
            ok_opt, err_opt = _compile_group(
                ctx.state.optimized, compile_args=opt_flags,
                output_file=opt_out, in_reference_root=False,
            )
            if not ok_orig:
                # Oracle re-build broke under this group's flags — config bug, not coder.
                group_failures.append(
                    f"[group {i}] reference re-build failed under `{group.compile_args}`: {err_orig}"
                )
                continue
            if not ok_opt:
                group_failures.append(
                    f"[group {i}] optimized compile failed under `{opt_flags}`: {err_opt}"
                )
                continue

            # Goldens for this group, byte-exact validated against optimized binary.
            case_failures: list[str] = []
            for case in group.golden:
                case_ok, diag = _run_test_case(ctx.state.optimized.executable, case)
                if not case_ok:
                    case_failures.append(diag)
            if case_failures:
                group_failures.append(
                    f"[group {i}] {len(case_failures)}/{len(group.golden)} golden(s) "
                    f"diverged (compile_args=`{group.compile_args}`):\n" + "\n".join(case_failures)
                )

            # Differentials for this group — compare both binaries directly.
            if group.differential:
                diffs = _run_differential_cases(
                    ctx.state.original.executable,
                    ctx.state.optimized.executable,
                    group.differential,
                )
                if diffs:
                    group_failures.append(
                        f"[group {i}] {len(diffs)}/{len(group.differential)} differential(s) "
                        f"diverged (compile_args=`{group.compile_args}`):\n" + "\n".join(diffs)
                    )

        summary = _gcovr_summary(
            ctx.state.repo_path,
            filter_source=ctx.state.repo_path / cfg.optimized_path,
        )
        if summary:
            _log("verify", "optimized coverage (gcovr, group 0):\n%s", summary)

        if group_failures:
            feedback = (
                f"Correctness tests failed for {cfg.optimized_path}:\n"
                + "\n".join(group_failures)
                + "\nFix the divergences. Keep behavior identical to the reference per group."
            )
            ctx.state.code_feedback = feedback
            attempt = _latest_attempt(ctx.state)
            if attempt is not None:
                attempt.outcome = "correctness failed"
                attempt.feedback = feedback
            return "fail"

        _log(
            "verify",
            "all correctness tests passed: %d golden(s) + %d differential(s) across %d group(s)",
            cfg.total_goldens(), cfg.total_differentials(), n_groups,
        )
        return "ok"

    @g.step
    async def safety_check_optimized(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Skip | Fail:
        _section("Candidate safety", category="verify")
        assert ctx.state.config is not None
        assert ctx.state.optimized is not None
        cfg = ctx.state.config
        if cfg.safety_mode == "off":
            _log("verify", "safety mode = off; skipping optimized safety check")
            return "skip"
        _log(
            "verify",
            "safety_check_optimized: mode=%s, %d group(s)",
            cfg.safety_mode, len(cfg.correctness_groups),
        )

        if cfg.safety_mode == "cbmc":
            ok, diag = _run_cbmc_check(
                (ctx.state.repo_path / cfg.optimized_path).resolve(),
                cbmc_args=cfg.cbmc_args,
            )
            if not ok:
                feedback = (
                    f"The optimized variant failed the CBMC safety check.\n"
                    f"{diag}\n"
                    f"Fix the unsafe access / undefined behavior before reattempting."
                )
                ctx.state.code_feedback = feedback
                attempt = _latest_attempt(ctx.state)
                if attempt is not None:
                    attempt.outcome = "safety failed"
                    attempt.feedback = feedback
                return "fail"
            _log("verify", "safety check (optimized, CBMC) passed")
            return "ok"

        selected = cfg.selected_safety_groups()
        if not selected:
            _log("verify", "safety.groups is empty; skipping optimized ASAN check")
            return "skip"
        group_failures: list[str] = []
        for i, group in selected:
            out = ctx.state.repo_path / BUILD_ROOT / f"optimized_safety_g{i}"
            combined = f"{group.compile_args} {cfg.safety_flags}"
            ok, err = _compile_group(
                ctx.state.optimized, compile_args=combined, output_file=out, in_reference_root=False,
            )
            if not ok:
                group_failures.append(f"[group {i}] sanitizer build failed: {err}")
                continue
            inputs = [c.args for c in group.golden] + list(group.differential)
            asan_failures = _run_asan_over_inputs(ctx.state.optimized.executable, inputs)
            if asan_failures:
                group_failures.append(
                    f"[group {i}] sanitizer reported {len(asan_failures)} issue(s) "
                    f"(compile_args=`{group.compile_args}`):\n" + "\n".join(asan_failures)
                )

        if group_failures:
            feedback = (
                f"The optimized variant failed the ASAN+UBSan safety check.\n"
                + "\n".join(group_failures)
                + "\nFix the unsafe access / undefined behavior before reattempting."
            )
            ctx.state.code_feedback = feedback
            attempt = _latest_attempt(ctx.state)
            if attempt is not None:
                attempt.outcome = "safety failed"
                attempt.feedback = feedback
            return "fail"
        _log("verify", "safety check (optimized, ASAN) passed across %d group(s)", len(selected))
        return "ok"

    @g.step
    async def profile_refactor(
        ctx: StepContext[PipelineStage, None, object],
    ) -> Ok | Fail | Skip:
        _section("Performance", category="benchmark")
        if not ctx.state.profile_enabled:
            _log("benchmark", "profile step disabled; skipping")
            return "skip"
        assert ctx.state.config is not None
        assert ctx.state.original is not None
        assert ctx.state.optimized is not None
        cfg = ctx.state.config
        _log(
            "benchmark",
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
            feedback = (
                f"The optimized variant {cfg.optimized_path} did not compile with "
                f"`{cfg.compiler.value} {cfg.performance_flags}`:\n{exc}"
            )
            ctx.state.code_feedback = feedback
            attempt = _latest_attempt(ctx.state)
            if attempt is not None:
                attempt.outcome = "performance build failed"
                attempt.feedback = feedback
            return "fail"
        try:
            (
                ctx.state.original_latencies,
                ctx.state.optimized_latencies,
            ) = _benchmark_pair(
                ctx.state.original,
                ctx.state.optimized,
                args=cfg.benchmark_args,
                runs=cfg.benchmark_runs,
            )
        except Exception as exc:
            feedback = f"Benchmark execution failed: {exc}"
            ctx.state.code_feedback = feedback
            attempt = _latest_attempt(ctx.state)
            if attempt is not None:
                attempt.outcome = "benchmark failed"
                attempt.feedback = feedback
            return "fail"

        original_stats = _benchmark_stats(ctx.state.original_latencies)
        optimized_stats = _benchmark_stats(ctx.state.optimized_latencies)
        original = original_stats.mean
        optimized = optimized_stats.mean
        if optimized <= 0:
            ctx.state.code_feedback = f"Invalid optimized latency: {optimized}"
            return "fail"
        speedup = original / optimized
        speedup_pct = (speedup - 1.0) * 100.0
        attempt = _latest_attempt(ctx.state)
        if attempt is not None:
            attempt.original_stats = original_stats
            attempt.optimized_stats = optimized_stats
            attempt.speedup_pct = speedup_pct
        _log(
            "benchmark",
            "profile:\n%s\n%s\nmean speedup=%.3fx (%+.2f%%) target>%.2f%%; "
            "samples=%d interleaved",
            _format_benchmark_stats("original", original_stats),
            _format_benchmark_stats("optimized", optimized_stats),
            speedup, speedup_pct, cfg.target_speedup, len(original_stats.samples),
        )
        if speedup_pct > cfg.target_speedup:
            if attempt is not None:
                attempt.outcome = "accepted"
            _write_benchmark_history(ctx.state)
            return "ok"
        feedback = (
            f"Speedup {speedup_pct:.2f}% did not exceed target "
            f"{cfg.target_speedup:.2f}% (original={original:.6f}s, "
            f"optimized={optimized:.6f}s).\n"
            f"{_format_benchmark_stats('original', original_stats)}\n"
            f"{_format_benchmark_stats('optimized', optimized_stats)}\n"
            "Pick a different optimization that actually moves the runtime."
        )
        ctx.state.code_feedback = feedback
        if attempt is not None:
            attempt.outcome = "performance rejected"
            attempt.feedback = feedback
        _write_benchmark_history(ctx.state)
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
        _section("Complete")
        assert ctx.state.config is not None
        cfg = ctx.state.config
        reports = "\n".join(
            f"    {i}. {stage}"
            for i, (stage, _) in enumerate(ctx.state.reports, start=1)
        )
        perf_line = ""
        if ctx.state.optimized_latencies:
            original_stats = _benchmark_stats(ctx.state.original_latencies)
            optimized_stats = _benchmark_stats(ctx.state.optimized_latencies)
            original = original_stats.mean
            optimized = optimized_stats.mean
            speedup = original / optimized if optimized else float("inf")
            speedup_pct = (speedup - 1.0) * 100.0
            perf_line = (
                f"  perf gate:   mean speedup={speedup:.3f}x ({speedup_pct:+.2f}%)\n"
                f"  {_format_benchmark_stats('original', original_stats)}\n"
                f"  {_format_benchmark_stats('optimized', optimized_stats)}\n"
                f"  benchmarks:  {ctx.state.repo_path / BUILD_ROOT / 'benchmark_history.json'}\n"
            )
        return (
            "Refactoring pipeline complete.\n"
            f"  config:      {ctx.state.config_path}\n"
            f"  compiler:    {cfg.compiler.value}\n"
            f"  sources:     {cfg.original_path} -> {cfg.optimized_path}\n"
            f"  perf flags:  {cfg.performance_flags!r}\n"
            f"  groups:      {len(cfg.correctness_groups)} "
            f"({cfg.total_goldens()} golden(s) + {cfg.total_differentials()} differential(s))\n"
            f"  safety:      {cfg.safety_mode}\n"
            f"  planner:     {ctx.state.planner_iterations} re-plan round(s)\n"
            f"  coder:       {ctx.state.coder_iterations} retry round(s)\n"
            + perf_line
            + "  attempts:\n"
            + _attempt_history_summary(ctx.state).replace("\n", "\n    ")
            + "\n"
            + f"  message reports ({len(ctx.state.reports)}):\n{reports}\n"
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
        .branch(g.match(TypeExpression[Ok]).to(safety_check_optimized))
        .branch(g.match(TypeExpression[Fail]).to(coder_retry_gate))
    )

    safety_check_original_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(bootstrap_context))
        .branch(g.match(TypeExpression[Skip]).to(bootstrap_context))
        .branch(g.match(TypeExpression[Fail]).to(failed))
    )

    safety_check_optimized_decision = (
        g.decision()
        .branch(g.match(TypeExpression[Ok]).to(profile_refactor))
        .branch(g.match(TypeExpression[Skip]).to(profile_refactor))
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
        g.edge_from(sanity_check_original).to(ok_or_fail_to(safety_check_original)),
        g.edge_from(safety_check_original).to(safety_check_original_decision),
        g.edge_from(bootstrap_context).to(ok_or_fail_to(plan_refactor)),
        g.edge_from(plan_refactor).to(ok_or_fail_to(code_refactor)),
        g.edge_from(code_refactor).to(code_refactor_decision),
        g.edge_from(test_refactor).to(test_refactor_decision),
        g.edge_from(safety_check_optimized).to(safety_check_optimized_decision),
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

    try:
        result = await graph.run(state=state)
        print(result)
    finally:
        for agent in (PLANNER_AGENT, CODER_AGENT, CONFIG_BUILDER_AGENT):
            await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
