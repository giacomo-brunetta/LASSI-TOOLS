from __future__ import annotations

from pathlib import Path

from .base import Agent, render_paths


class CoderAgent(Agent):
    """Generic coder. Implements or repairs one planned optimization safely."""

    name = "coder"
    model = "inherit"
    allowed_skills: list[str] = []

    def build_task_prompt(
        self,
        *,
        plan_message: str,
        target_file: Path,
        reference_file: Path,
        notes: str = "",
    ) -> str:
        body = render_paths(
            {
                "target file":    target_file,
                "reference file": reference_file,
            }
        )
        body += f"\n\nPlanner message:\n\n{plan_message.strip()}"
        body += "\n\nReturn the complete Markdown changes report in your final reply."
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
