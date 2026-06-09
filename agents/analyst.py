from __future__ import annotations

from pathlib import Path

from .base import Agent


class AnalystAgent(Agent):
    name = "analyst"
    model = "inherit"
    allowed_skills: list[str] = []

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        notes: str = "",
    ) -> str:
        body = f"input file:  {input_path}\noutput file: {output_path}"
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
