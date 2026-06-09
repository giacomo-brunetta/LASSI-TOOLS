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
        input_path: Path,
        output_path: Path,
        target_file: Path,
        reference_file: Path,
        notes: str = "",
    ) -> str:
        body = render_paths(
            {
                "input file":     input_path,
                "output file":    output_path,
                "target file":    target_file,
                "reference file": reference_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
