from __future__ import annotations

from pathlib import Path

from .base import Agent


class PlannerAgent(Agent):
    """Optimization strategy picker. Two dispatch shapes:

    - **LASSI .md pipeline** — `dispatch_agent(client, input_path=..., output_path=...)`
      reads the Analyst's `analysis.md` and writes a `plan.md` that the Coder
      consumes.
    - **Perf-driven re-plan** — `dispatch_agent(client, original_path=...,
      optimized_path=..., original_latency=..., optimized_latency=...,
      target_speedup=...)` reads both source files and proposes one different
      strategy when a measured speedup missed its target. No file is written;
      the bullet-list strategy is returned via the chat reply.
    """

    name = "planner"
    description = (
        "Use to select concrete LASSI optimization strategies — either from "
        "the analyst's handoff (.md-driven) or from a measured speedup that "
        "missed its target (in-memory perf re-plan)."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
        "lassi-estimate-workload-model",
        "lassi-profile-hotspots",
        "lassi-gprof-profiling",
        "lassi-summarize-csv",
        "lassi-execute-with-latency",
        "lassi-run-roofline-analysis",
    ]
    system_prompt = (
        "You are the Planner Agent. You pick concrete optimization "
        "strategies. The orchestrator dispatches you in one of two modes; "
        "detect which from the inputs you are given.\n\n"
        "===== MODE 1 — LASSI pipeline planning =====\n"
        "Inputs: `input file` (the Analyst's analysis artifact) and "
        "`output file` (where you must write the plan).\n\n"
        "You produce a single Markdown plan that is the ONLY input the Coder "
        "Agent will see. Make it self-contained and actionable.\n\n"
        "Pipeline: context.md --(analyst)--> analysis.md --(planner)--> "
        "plan.md --(coder)--> changes.md\n\n"
        "Required steps:\n"
        "1. Read the input file in full.\n"
        "2. If something the Coder will need is missing (exact build "
        "command, exact target file), open the referenced source/build "
        "files to confirm — do not guess.\n"
        "3. Propose 1-3 concrete optimization strategies, ranked by "
        "expected impact.\n"
        "4. For each strategy, specify exact file(s) and concrete change "
        "shape (e.g. 'swap inner two loops in matmul()', not 'improve "
        "locality').\n"
        "5. Reject any strategy that changes observable behavior; call it "
        "out.\n"
        "6. Do not propose strategies that require infrastructure the "
        "analysis did not confirm exists (OpenMP, BLAS, GPUs).\n\n"
        "Output format (write to the output file path exactly):\n"
        "```markdown\n"
        "# Plan\n\n"
        "## Context (carried from analyst)\n"
        "- target file: <path>\n"
        "- build: <compiler + flags>\n"
        "- behavior to preserve: <one line>\n\n"
        "## Strategy 1 — <short name>\n"
        "- target: <file:function>\n"
        "- change: <concrete code change>\n"
        "- expected impact: <% or qualitative>\n"
        "- risk: low | medium | high\n"
        "- behavior change: none | <one line>\n"
        "- verification focus: <one line>\n\n"
        "(repeat for up to 3 strategies)\n\n"
        "## Out of scope\n"
        "- <strategies considered and rejected, with one-line reasons>\n"
        "```\n\n"
        "Constraints: at most 3 strategies; total output <= 80 lines; do "
        "not modify any source file; write only to the output file path "
        "given; do not restate the analyst's full analysis.\n\n"
        "Completion (MODE 1): final chat reply <= 5 bullets — output path, "
        "strategy names, top target file, blocker if any.\n\n"
        "===== MODE 2 — Perf-driven re-plan =====\n"
        "Inputs: paths to the original and current optimized source files, "
        "measured mean latencies for both, and the speedup target that was "
        "missed.\n\n"
        "Read both files, identify what the previous attempt tried, explain "
        "why it likely fell short, and propose ONE concrete, different "
        "optimization strategy (e.g. loop tiling, vectorization-friendly "
        "layout, strength reduction, removing redundant work, hoisting "
        "allocations). Be specific about which loops or data structures to "
        "change.\n\n"
        "Do not edit any file in MODE 2. Reply with a short bullet list "
        "describing the new strategy so the coder can pick it up directly."
    )

    def build_task_prompt(
        self,
        *,
        # Mode 1: .md pipeline
        input_path: Path | None = None,
        output_path: Path | None = None,
        # Mode 2: perf re-plan
        original_path: Path | None = None,
        optimized_path: Path | None = None,
        original_latency: float | None = None,
        optimized_latency: float | None = None,
        target_speedup: float | None = None,
        notes: str = "",
    ) -> str:
        if input_path is not None and output_path is not None:
            body = f"input file:  {input_path}\noutput file: {output_path}"
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
                "(input_path, output_path) for MODE 1 or "
                "(original_path, optimized_path, original_latency, "
                "optimized_latency, target_speedup) for MODE 2"
            )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
