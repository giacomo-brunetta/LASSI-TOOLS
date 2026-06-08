from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean

from openai_codex import AsyncCodex, Sandbox
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from lassi.core.compiler import Compiler, CompilerTool
from lassi.core.executer import FunctionalValidator, WrongOutput
from lassi.core.source_file import SourceFile
from lassi.profiling.profiler import Timer
from lassi.verification.checks import parse_floats_from_text, summarize_numeric_diff


logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

GOLDEN_OUTPUTS = [
    ("1 1 1", "1 \n"),
    ("2 3 4", "1 0 0 0 \n0 1 0 0 \n"),
    ("4 2 3", "1 0 0 \n0 1 0 \n0 0 0 \n0 0 0 \n"),
    ("3 5 2", "1 0 \n0 1 \n0 0 \n"),
    ("5 3 5", "1 0 0 0 0 \n0 1 0 0 0 \n0 0 1 0 0 \n0 0 0 0 0 \n0 0 0 0 0 \n"),
    ("3 1 4", "1 0 0 0 \n0 0 0 0 \n0 0 0 0 \n"),
    ("8 6 8", "1 0 0 0 0 0 0 0 \n0 1 0 0 0 0 0 0 \n0 0 1 0 0 0 0 0 \n0 0 0 1 0 0 0 0 \n0 0 0 0 1 0 0 0 \n0 0 0 0 0 1 0 0 \n0 0 0 0 0 0 0 0 \n0 0 0 0 0 0 0 0 \n"),
]

BENCHMARK_ARGS = "128 128 128"
BENCHMARK_RUNS = 5
BUILD_ROOT = Path(".verify/refactoring")


def clang_source(path: Path) -> SourceFile:
    return SourceFile(path, compiler_tool=CompilerTool(Compiler.CLANG))


def validate_golden_outputs(source: SourceFile, label: str) -> None:
    for args, golden_output in GOLDEN_OUTPUTS:
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


def benchmark(source: SourceFile) -> list[float]:
    latencies = []
    for _ in range(BENCHMARK_RUNS):
        report = source.execute(args=BENCHMARK_ARGS, profiler=Timer())
        latencies.append(report.latency)
    return latencies


@dataclass
class RefactoringState:
    repo_path: Path = field(default_factory=lambda: Path.cwd().resolve())
    original_path: Path = field(default_factory=lambda: Path("test.c"))
    optimized_path: Path = field(default_factory=lambda: Path("optimized.c"))
    original: SourceFile | None = None
    optimized: SourceFile | None = None
    codex_result: str | None = None
    correctness_passed: bool = False
    original_latencies: list[float] = field(default_factory=list)
    optimized_latencies: list[float] = field(default_factory=list)
    error: str | None = None


@dataclass
class PrepareSources(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> RefactorWithCodex | Failed:
        logger.info("preparing original and optimized source files")
        try:
            ctx.state.original = clang_source(ctx.state.original_path)
            ctx.state.optimized = clang_source(ctx.state.optimized_path)
            ctx.state.optimized.write(ctx.state.original.read())
            BUILD_ROOT.mkdir(parents=True, exist_ok=True)
            return RefactorWithCodex()
        except Exception as exc:
            ctx.state.error = f"source preparation failed: {exc}"
            return Failed()


@dataclass
class RefactorWithCodex(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> CheckCorrectnessO0 | Failed:
        logger.info("asking Codex to optimize %s", ctx.state.optimized_path)
        try:
            prompt = "\n".join([
                f"Repository: {ctx.state.repo_path}",
                "",
                f"Optimize the C program in {ctx.state.optimized_path} for lower runtime latency.",
                "",
                "Constraints:",
                f"- Modify only {ctx.state.optimized_path}; do not modify {ctx.state.original_path}.",
                "- Preserve the command-line interface and exact stdout for every valid input.",
                "- Keep the implementation in portable C accepted by clang.",
                "- Do not alter the graph or golden outputs.",
                "- Run a basic compile check before finishing.",
                "- Summarize the optimization in the final response.",
            ])
            async with AsyncCodex() as codex:
                thread = await codex.thread_start(
                    model="gpt-5.4",
                    cwd=str(ctx.state.repo_path),
                    sandbox=Sandbox.workspace_write,
                )
                result = await thread.run(prompt)
            ctx.state.codex_result = result.final_response
            if not ctx.state.optimized_path.exists():
                raise FileNotFoundError(f"Codex did not create {ctx.state.optimized_path}")
            ctx.state.optimized = clang_source(ctx.state.optimized_path)
            return CheckCorrectnessO0()
        except Exception as exc:
            ctx.state.error = f"Codex refactoring failed: {exc}"
            return Failed()


@dataclass
class CheckCorrectnessO0(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> CompileO3 | Failed:
        logger.info("checking original and optimized correctness with clang -O0")
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original.compile(kwds="-O0", output_file=BUILD_ROOT / "original_O0")
            ctx.state.optimized.compile(kwds="-O0", output_file=BUILD_ROOT / "optimized_O0")
            validate_golden_outputs(ctx.state.original, "original")
            validate_golden_outputs(ctx.state.optimized, "optimized")
            ctx.state.correctness_passed = True
            return CompileO3()
        except Exception as exc:
            ctx.state.error = f"-O0 correctness check failed: {exc}"
            return Failed()


@dataclass
class CompileO3(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> BenchmarkLatency | Failed:
        logger.info("compiling original and optimized sources with clang -O3")
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original.compile(kwds="-O3", output_file=BUILD_ROOT / "original_O3")
            ctx.state.optimized.compile(kwds="-O3", output_file=BUILD_ROOT / "optimized_O3")
            return BenchmarkLatency()
        except Exception as exc:
            ctx.state.error = f"-O3 compilation failed: {exc}"
            return Failed()


@dataclass
class BenchmarkLatency(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> Success | Failed:
        logger.info("benchmarking original and optimized -O3 binaries")
        try:
            assert ctx.state.original is not None
            assert ctx.state.optimized is not None
            ctx.state.original_latencies = benchmark(ctx.state.original)
            ctx.state.optimized_latencies = benchmark(ctx.state.optimized)
            return Success()
        except Exception as exc:
            ctx.state.error = f"latency benchmark failed: {exc}"
            return Failed()


@dataclass
class Success(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> End[str]:
        original = mean(ctx.state.original_latencies)
        optimized = mean(ctx.state.optimized_latencies)
        speedup = original / optimized if optimized else float("inf")
        return End(
            "Refactoring passed correctness checks.\n"
            f"Original -O3 mean latency: {original:.6f} s\n"
            f"Optimized -O3 mean latency: {optimized:.6f} s\n"
            f"Speedup: {speedup:.3f}x\n"
            f"Codex summary: {ctx.state.codex_result}"
        )


@dataclass
class Failed(BaseNode[RefactoringState, None, str]):
    async def run(self, ctx: GraphRunContext[RefactoringState, None]) -> End[str]:
        return End(f"Refactoring pipeline failed: {ctx.state.error}")


async def main() -> None:
    graph = Graph(
        nodes=(PrepareSources, RefactorWithCodex, CheckCorrectnessO0, CompileO3, BenchmarkLatency, Success, Failed),
        state_type=RefactoringState,
        run_end_type=str,
    )
    state = RefactoringState()
    result = await graph.run(PrepareSources(), state=state)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
