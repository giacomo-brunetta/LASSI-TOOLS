from __future__ import annotations

from pathlib import Path

from .base import Agent


class CCodeOptimizerAgent(Agent):
    """Subagent that edits one C source file to lower its runtime latency."""

    name = "c-optimizer"
    description = (
        "Optimize a single C source file for lower runtime latency without changing "
        "its observable behavior."
    )
    system_prompt = (
        "You are a C performance specialist. You will be given the path of a single C "
        "file to optimize and the path of a reference file you must NOT touch.\n\n"
        "Rules:\n"
        "- Edit only the file the user names; never touch any other file.\n"
        "- Preserve the command-line interface and exact stdout for every valid input.\n"
        "- Keep the implementation in portable C accepted by the project's compiler.\n"
        "- Do not alter graph structure or golden outputs.\n"
        "- Run a compile check (e.g. `clang -O3 <file> -o /tmp/check`) before finishing.\n"
        "- Reply with a one-paragraph summary of the optimization you applied."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
    model = "inherit"
    allowed_skills = [
        "lassi-execute-with-latency",
        "lassi-build-sanitized",
        "lassi-profile-hotspots",
        "lassi-collect-perf-stats",
    ]

    def build_task_prompt(
        self,
        *,
        optimized_path: Path,
        original_path: Path,
        compiler: str,
        performance_flags: str,
        error: str | None = None,
        strategy: str | None = None,
    ) -> str:
        sections: list[str] = []
        if strategy:
            sections.append(
                "Apply this strategy from the planner verbatim:\n" + strategy.strip()
            )
        if error:
            sections.append(
                "The previous attempt failed verification with this error:\n"
                + error.strip()
                + "\n\nFix it before re-applying any optimization."
            )
        constraints = [
            f"Edit only {optimized_path}; do not modify {original_path}.",
            "Preserve the command-line interface and exact stdout for every valid input.",
            f"Keep the implementation in portable C accepted by {compiler}.",
            "Do not alter the graph or golden outputs.",
            f"Run a `{compiler} {performance_flags} {optimized_path} -o /tmp/check` "
            "compile check before finishing.",
            "Return a short summary of the optimization applied.",
        ]
        sections.append("Constraints:\n- " + "\n- ".join(constraints))
        return "\n\n".join(sections)
