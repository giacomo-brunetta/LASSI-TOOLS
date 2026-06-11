from __future__ import annotations

from pathlib import Path

from .base import Agent


class ConfigBuilderAgent(Agent):
    """Bootstraps a `graph_code_test.json`-shaped pipeline config from a kernel.

    Discovers the source files, picks a compiler + flag pair, infers a
    benchmark argument shape from the program's CLI, generates a small set of
    golden (args, stdout) cases by actually running the reference binary,
    and returns the final JSON to the orchestrator.
    """

    name = "config-builder"
    model = "inherit"
    allowed_skills: list[str] = []

    def build_task_prompt(
        self,
        *,
        repo_path: Path,
        target_path: Path | None = None,
        target_hint: str | None = None,
        compiler_hint: str | None = None,
        correctness_flags_hint: str | None = None,
        performance_flags_hint: str | None = None,
        benchmark_hint: str | None = None,
        scope_hint: list[Path] | None = None,
        notes: str = "",
    ) -> str:
        items: dict[str, object] = {
            "repo path": repo_path,
        }
        if target_path is not None:
            items["target source file (repo-relative)"] = str(target_path)
        elif target_hint:
            items["target kernel hint"] = target_hint
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
        if target_path is not None:
            body += (
                f"\n\nThe target source file is `{target_path}` (repo-relative). "
                "Use this exact path for `sources.original` — do NOT substitute "
                "a different file even if other candidates exist in the tree."
            )
        elif target_hint:
            body += (
                f"\n\nThe target kernel is {target_hint!r}: pick the source file "
                f"whose path or filename matches this token (e.g. `.../{target_hint}/"
                f"{target_hint}.c` in a PolyBench-style layout). Do NOT pick a "
                "different kernel even if it appears first alphabetically."
            )
        body += (
            "\n\nAll paths in the JSON (sources.original, sources.optimized, "
            "every scope[*]) MUST be relative to the repo root. Never emit "
            "absolute paths and never include a leading `/workspace/`."
        )
        body += "\n\nReturn only the complete JSON config in your final reply."
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
