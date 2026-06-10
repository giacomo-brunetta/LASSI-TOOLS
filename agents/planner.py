from __future__ import annotations

from pathlib import Path

from .base import Agent


class PlannerAgent(Agent):
    """Optimization strategy picker. Two dispatch shapes:

    - **Message pipeline** — `dispatch_agent(context_message=...)` reads the
      supplied context, inspects the source, and returns a Markdown plan that
      the orchestrator passes directly to the Coder.
    - **Perf-driven re-plan** — `dispatch_agent(original_path=...,
      optimized_path=..., original_latency=..., optimized_latency=...,
      target_speedup=...)` reads both source files and proposes one different
      strategy when a measured speedup missed its target. No file is written;
      the bullet-list strategy is returned via the chat reply.
    """

    name = "planner"
    model = "inherit"
    allowed_skills: list[str] = []
    access_mode = "read"

    def build_task_prompt(
        self,
        *,
        # Mode 1: message pipeline
        context_message: str | None = None,
        # Mode 2: perf re-plan
        original_path: Path | None = None,
        optimized_path: Path | None = None,
        original_latency: float | None = None,
        optimized_latency: float | None = None,
        target_speedup: float | None = None,
        notes: str = "",
    ) -> str:
        if context_message is not None:
            body = (
                "Pipeline context message:\n\n"
                f"{context_message.strip()}\n\n"
                "Return the complete Markdown plan in your final reply."
            )
        elif (
            original_path is not None
            and optimized_path is not None
            and original_latency is not None
            and optimized_latency is not None
            and target_speedup is not None
        ):
            body = "\n".join(
                [
                    f"Read both {original_path} and the current {optimized_path}.",
                    "",
                    f"Measured original mean latency: {original_latency:.6f} s",
                    f"Measured optimized mean latency: {optimized_latency:.6f} s",
                    f"Target speedup (strict, percent): > {target_speedup:.2f}%",
                    "",
                    "Identify what the previous attempt tried, explain why it "
                    "fell short, and propose ONE concrete, different "
                    "optimization strategy.",
                    "Reply with a short bullet list of the new strategy.",
                ]
            )
        else:
            raise TypeError(
                "PlannerAgent.build_task_prompt requires either "
                "context_message for MODE 1 or "
                "(original_path, optimized_path, original_latency, "
                "optimized_latency, target_speedup) for MODE 2"
            )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
