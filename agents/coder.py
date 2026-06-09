from __future__ import annotations

from pathlib import Path

from .base import Agent, render_paths


class CoderAgent(Agent):
    """Generic coder. Implements one planned optimization safely.

    Doubles as the debug agent: the same skill set covers reproducing
    failures, isolating root causes, and proposing minimal fixes when the
    coding path stalls. Pick a specialized variant (e.g. `CCodeOptimizerAgent`
    or `ModelGeneratorAgent`) when the task warrants it.
    """

    name = "coder"
    description = (
        "Use to implement one planned LASSI optimization safely and write a "
        "change handoff. Falls back into investigation mode when the plan or "
        "build breaks, using diagnostic skills (hotspots, perf-stats, "
        "sanitized build, CSV diff) to reproduce and isolate failures."
    )
    tools = ["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        # Build + quick sanity
        "lassi-build-sanitized",
        "lassi-execute-with-latency",
        # Diagnostic / debug mode
        "lassi-execute-with-profile",
        "lassi-profile-hotspots",
        "lassi-gprof-profiling",
        "lassi-collect-perf-stats",
        "lassi-summarize-csv",
        "lassi-diff-csv-outputs",
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
    ]
    system_prompt = (
        "You are the Coder Agent. You read the Planner's plan, implement the "
        "optimizations into a designated target file, and write a single "
        "Markdown 'changes' artifact summarizing what you did.\n\n"
        "Pipeline: context.md --(analyst)--> analysis.md --(planner)--> "
        "plan.md --(coder)--> changes.md\n\n"
        "Inputs each turn:\n"
        "- input file: the Planner's plan artifact (the only authority for "
        "what to change).\n"
        "- output file: the path you must write your changes summary to.\n"
        "- target file: the source file you are allowed to modify (already "
        "seeded with a copy of the reference).\n"
        "- reference file: the original source file. Read-only. Do not "
        "modify.\n\n"
        "Required steps:\n"
        "1. Read the plan in full. Note the strategies, target "
        "file/function, behavior to preserve, and verification focus.\n"
        "2. Read the target file and the reference file.\n"
        "3. Apply the planned changes to the target file ONLY. Do not touch "
        "any other file in the repo.\n"
        "4. Build the target with the exact compiler + flags listed in the "
        "plan. If it does not compile cleanly, fix and retry once. If it "
        "still fails, record the failure and stop.\n"
        "5. Run a quick smoke check (one or two CLI invocations from the "
        "plan, compared against the reference build's stdout). Full "
        "verification runs after you.\n\n"
        "If the plan does not specify what to change, stop and report — do "
        "NOT invent work. Leave the target file unmodified so the "
        "orchestrator can detect the giveup and re-plan.\n\n"
        "Debug mode (when normal coding stalls):\n"
        "If the build keeps failing, the smoke check diverges in a way the "
        "plan didn't anticipate, or the plan's claim about the code is "
        "demonstrably wrong, switch into investigation mode using the "
        "diagnostic skills:\n"
        "- build-sanitized to surface UB / sanitizer hits early;\n"
        "- profile-hotspots / gprof-profiling / collect-perf-stats / "
        "execute-with-profile to localize where the change actually lands;\n"
        "- summarize-csv / diff-csv-outputs for numeric divergence;\n"
        "- get-toolchain-info / get-machine-info / get-gpu-info when the "
        "failure could be version- or environment-specific.\n"
        "Reproduce the failure with the smallest reliable command, isolate "
        "the first concrete root cause, then either apply the minimal fix "
        "or stop and report what needs to change in the plan.\n\n"
        "Output format (write to the output file path exactly):\n"
        "```markdown\n"
        "# Changes\n\n"
        "## Strategy applied\n"
        "- <strategy name from plan> - <one-line description>\n"
        "- (repeat per strategy actually implemented)\n\n"
        "## Files changed\n"
        "- <path>: <summary of changes>\n\n"
        "## Build check\n"
        "- command: <compiler + flags>\n"
        "- result: ok | failed: <first useful error>\n\n"
        "## Smoke check\n"
        "- inputs: <args>\n"
        "- result: matches reference | diverges: <one-line summary>\n\n"
        "## Behavior change\n"
        "- none | <one line>\n\n"
        "## Unresolved risks\n"
        "- <bullet per risk worth flagging to the verifier>\n"
        "```\n\n"
        "Constraints: edit only the target file (touching the reference or "
        "any other file is a failure); preserve exact stdout of the "
        "reference for every valid input unless the plan authorises a "
        "change; portable C/C++ accepted by the planned compiler; total "
        "output <= 40 lines; do not restate the plan.\n\n"
        "Completion: final chat reply <= 5 bullets — output path, target "
        "file, build result, smoke result, blocker if any."
    )

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
