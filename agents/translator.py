from __future__ import annotations

from pathlib import Path

from .base import Agent, render_paths


class TranslatorAgent(Agent):
    name = "translator"
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
    ]

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        source_file: Path,
        notes: str = "",
    ) -> str:
        body = render_paths(
            {
                "input file":  input_path,
                "output file": output_path,
                "source file": source_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
