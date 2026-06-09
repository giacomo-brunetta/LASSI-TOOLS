from __future__ import annotations

from pathlib import Path

from .base import Agent


class ConfigBuilderAgent(Agent):
    """Bootstraps a `graph_code_test.json`-shaped pipeline config from a kernel.

    Discovers the source files, picks a compiler + flag pair, infers a
    benchmark argument shape from the program's CLI, generates a small set of
    golden (args, stdout) cases by actually running the reference binary,
    and writes the final JSON to the path the orchestrator gives it.
    """

    name = "config-builder"
    description = (
        "Use to generate or update a graph_code_test.json-style pipeline "
        "config (sources, compiler, scope, flags, arguments, golden outputs) "
        "from a kernel source."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-execute-with-latency",
        "lassi-build-sanitized",
    ]
    system_prompt = (
        "You are the Config Builder Agent. You produce a single JSON config "
        "for the LASSI graph_code_test pipeline. The JSON must match this "
        "exact shape (omit no keys):\n\n"
        "```json\n"
        "{\n"
        "  \"sources\":   {\"original\": \"<path>\", \"optimized\": \"<path>\"},\n"
        "  \"compiler\":  \"clang|gcc|clang++|g++\",\n"
        "  \"scope\":     [\"<path>\", ...],\n"
        "  \"flags\":     {\"correctness\": \"<flags>\", \"performance\": \"<flags>\"},\n"
        "  \"arguments\": {\n"
        "    \"benchmark\":      \"<CLI args for a stable timing run>\",\n"
        "    \"benchmark_runs\": <int>,\n"
        "    \"target_speedup\": <float, percent>,\n"
        "    \"golden\":         [{\"args\": \"<CLI>\", \"stdout\": \"<exact bytes>\"}, ...]\n"
        "  }\n"
        "}\n"
        "```\n\n"
        "You are given:\n"
        "- repo path: the working directory containing the source(s).\n"
        "- output file: the JSON path you must write.\n"
        "- (optional) compiler hint, flag hints, benchmark hint, scope "
        "hint.\n\n"
        "Required steps:\n"
        "1. Explore the repo and pick the single source file to optimize "
        "(typically the only top-level .c/.cpp/.cu with a main()). Identify "
        "its CLI shape (argv parsing).\n"
        "2. Pick a compiler (default `clang` if unspecified) and a "
        "correctness/performance flag pair (default `-O0 -lm` / "
        "`-O3 -lm`).\n"
        "3. Build the reference once with the correctness flags to confirm "
        "the binary works.\n"
        "4. Generate 5-8 golden cases that exercise distinct input shapes "
        "(small, square, rectangular, edge sizes). For each, run the "
        "reference binary and capture its EXACT stdout (preserve trailing "
        "newlines and spaces verbatim).\n"
        "5. Choose a benchmark `args` line large enough to take >50ms but "
        "not so large that a single run is painful; default "
        "`benchmark_runs` to 5 and `target_speedup` to 0.0 unless the "
        "user specified otherwise.\n"
        "6. Populate `scope` with: the source path, the optimized path, "
        "and any build/output directories the pipeline writes into "
        "(`.verify` by default).\n"
        "7. Write the JSON to the output file path. Validate it parses.\n\n"
        "Constraints: do not invent stdout — every golden entry must come "
        "from an actual run. Do not modify the source file. Write only to "
        "the output file path given.\n\n"
        "Completion: final chat reply <= 5 bullets — output path, compiler "
        "+ flags, benchmark args, number of golden cases, blocker if any."
    )

    def build_task_prompt(
        self,
        *,
        repo_path: Path,
        output_path: Path,
        compiler_hint: str | None = None,
        correctness_flags_hint: str | None = None,
        performance_flags_hint: str | None = None,
        benchmark_hint: str | None = None,
        scope_hint: list[Path] | None = None,
        notes: str = "",
    ) -> str:
        items: dict[str, object] = {
            "repo path":   repo_path,
            "output file": output_path,
        }
        if compiler_hint:
            items["compiler hint"] = compiler_hint
        if correctness_flags_hint:
            items["correctness flags hint"] = correctness_flags_hint
        if performance_flags_hint:
            items["performance flags hint"] = performance_flags_hint
        if benchmark_hint:
            items["benchmark args hint"] = benchmark_hint
        if scope_hint:
            items["scope hint"] = ", ".join(str(p) for p in scope_hint)
        body = "\n".join(f"{k}: {v}" for k, v in items.items())
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
