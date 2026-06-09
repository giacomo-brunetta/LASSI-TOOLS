from __future__ import annotations

from pathlib import Path

from .base import Agent, render_paths


class ModelGeneratorAgent(Agent):
    name = "model-generator"
    model = "inherit"
    allowed_skills = [
        "lassi-export-model-to-pt",
        "lassi-compile-torch-to-mlir",
        "lassi-synthesize-tosa-with-soda",
        "lassi-get-toolchain-info",
    ]

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        variants_file: Path,
        notes: str = "",
    ) -> str:
        body = render_paths(
            {
                "input file":    input_path,
                "output file":   output_path,
                "variants file": variants_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
