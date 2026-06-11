from __future__ import annotations

from pathlib import Path

from .base import Agent, render_paths


class CoderAgent(Agent):
    """Generic coder. Implements or repairs one planned optimization safely."""

    name = "coder"
    model = "inherit"
    allowed_skills: list[str] = [
        # Function-level hotspot picker — fast first look at where time goes.
        "lassi-gprof-profiling",
        # Sample-based hotspot list (perf record on Linux, sample on macOS).
        "lassi-profile-hotspots",
        # IPC + cache/branch counters via perf stat.
        "lassi-collect-perf-stats",
        # Stable a/b timing via hyperfine.
        "lassi-run-benchmark",
        # Quick wall-clock check (one shot).
        "lassi-execute-with-latency",
        # Wall-clock + CPU/GPU power probe.
        "lassi-execute-with-profile",
        # FLOPs / bytes / arithmetic intensity estimate.
        "lassi-estimate-workload-model",
        # Roofline placement against hardware ceilings.
        "lassi-run-roofline-analysis",
        # Reference vs candidate roofline diff.
        "lassi-compare-roofline",
        # Aggregate benchmark + perf-stat + hotspot into a verdict.
        "lassi-compare-performance",
        # CPU/cache/ISA fingerprint — informs blocking, vector widths, etc.
        "lassi-get-machine-info",
        # Toolchain versions — surface gcc/clang/LLVM mismatches early.
        "lassi-get-toolchain-info",
    ]

    def build_task_prompt(
        self,
        *,
        plan_message: str,
        target_file: Path,
        reference_file: Path,
        context_summary: str = "",
        notes: str = "",
    ) -> str:
        body = (
            "This is a fresh task session. Read the context summary first and "
            "silently compress it into: current state, prior attempts, measured "
            "evidence, constraints, and the next task. Treat that summary as "
            "authoritative over any assumptions.\n\n"
            f"{context_summary.strip()}\n\n"
        )
        body += render_paths(
            {
                "target file":    target_file,
                "reference file": reference_file,
            }
        )
        body += f"\n\nPlanner message:\n\n{plan_message.strip()}"
        body += (
            "\n\nMandatory execution requirements:\n"
            "- Invoke `lassi-get-machine-info` before choosing architecture- or "
            "cache-sensitive parameters.\n"
            "- Use `lassi-run-benchmark` before and after every source-changing "
            "attempt. Do not skip profiling for a small or one-line change.\n"
            "- Use at least one diagnostic performance skill when the measured "
            "result is neutral, surprising, or regresses.\n"
            "- Report the actual profiling evidence; `n/a` or `profiling skipped` "
            "is not acceptable for a source-changing attempt.\n\n"
            "Return the complete Markdown changes report in your final reply."
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body
