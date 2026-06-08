from __future__ import annotations

from pathlib import Path

from .base import Agent


class PlannerAgent(Agent):
    """Subagent that proposes a new optimization strategy when a target was missed."""

    name = "planner"
    description = (
        "Propose a concrete optimization strategy for a C file when the previous attempt "
        "missed the speedup target."
    )
    system_prompt = (
        "You are a performance planner. You will be given an original C file, the current "
        "optimized C file, the measured latencies of both, and the speedup target that was "
        "missed.\n\n"
        "Read both files, identify what the previous attempt tried, explain why it likely "
        "fell short, and propose ONE concrete, different optimization strategy (e.g. loop "
        "tiling, vectorization-friendly layout, strength reduction, removing redundant "
        "work, hoisting allocations). Be specific about which loops or data structures to "
        "change.\n\n"
        "Do not edit any file. Reply with a short bullet list describing the new strategy "
        "so it can be handed directly to a coder."
    )
    tools = ["Read", "Glob", "Grep"]
    model = "inherit"
    allowed_skills = [
        "lassi-profile-hotspots",
        "lassi-gprof-profiling",
        "lassi-summarize-csv",
        "lassi-estimate-workload-model",
        "lassi-execute-with-latency",
        "lassi-run-roofline-analysis",
    ]

    def build_task_prompt(
        self,
        *,
        original_path: Path,
        optimized_path: Path,
        original_latency: float,
        optimized_latency: float,
        target_speedup: float,
    ) -> str:
        return "\n".join(
            [
                f"Read both {original_path} and the current {optimized_path}.",
                "",
                f"Measured original mean latency: {original_latency:.6f} s",
                f"Measured optimized mean latency: {optimized_latency:.6f} s",
                f"Target speedup (strict, percent): > {target_speedup:.2f}%",
                "",
                "Identify what the previous attempt tried, explain why it fell short, "
                "and propose ONE concrete, different optimization strategy.",
                "Reply with a short bullet list of the new strategy.",
            ]
        )
