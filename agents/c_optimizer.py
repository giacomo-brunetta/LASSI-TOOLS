from __future__ import annotations

from pathlib import Path

from .base import Agent


class CCodeOptimizerAgent(Agent):
    """Subagent that edits one C source file to lower its runtime latency."""

    name = "c-optimizer"
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
