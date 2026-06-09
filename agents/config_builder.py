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
    model = "inherit"
    allowed_skills: list[str] = []

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
