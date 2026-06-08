"""Python specifications for the canonical LASSI agent set.

Each class mirrors the corresponding `.md` file under `~/.claude/agents/` so it
can be registered with the Claude Agent SDK directly. The `name`, `tools`, and
behavioral contract are kept faithful to the original markdown; `allowed_skills`
scopes which LASSI skills (`lassi-*`) each agent may invoke through the Skill
tool.

These classes share the SDK `name` `"planner"` with the local
`agents.planner.PlannerAgent` used by `graph_code_test.py`; only one should be
registered at a time. Choose the variant matching the workflow you're driving.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .base import Agent


def _render_paths(items: Mapping[str, Path]) -> str:
    return "\n".join(f"{key}: {value}" for key, value in items.items())


# ---------------------------------------------------------------------------
# Phase agents
# ---------------------------------------------------------------------------


class AnalystAgent(Agent):
    name = "analyst"
    description = (
        "Use for minimal actionable codebase analysis before LASSI optimization "
        "or translation work."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
    ]
    system_prompt = (
        "You are the Analyst Agent. You produce a single Markdown analysis "
        "artifact that is the ONLY input the Planner Agent will see. Make it "
        "self-contained.\n\n"
        "Pipeline: context.md --(analyst)--> analysis.md --(planner)--> "
        "plan.md --(coder)--> changes.md\n\n"
        "Given an input file (bootstrap context) and an output file path:\n"
        "1. Read the input file.\n"
        "2. Read the source file(s) it references plus the build files "
        "(Makefile, CMakeLists, etc.) needed to confirm how the program is "
        "built and run.\n"
        "3. Identify the kernel (purpose, entry point, call path).\n"
        "4. Identify the compile/run interface (compiler, flags, CLI args, "
        "env vars).\n"
        "5. List 1-5 refactoring targets with reasons.\n"
        "6. State assumptions and unknowns explicitly.\n\n"
        "Do not invent file names. Do not write to any other artifact. Do not "
        "read other LASSI/*.md files."
    )

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


class LassiPlannerAgent(Agent):
    """LASSI-pipeline Planner (reads analysis.md, writes plan.md).

    Distinct from `agents.planner.PlannerAgent`, which is the replan helper
    used by `graph_code_test.py`. Both register under SDK name `"planner"`.
    """

    name = "planner"
    description = (
        "Use to select concrete LASSI optimization strategies from the "
        "analyst's handoff."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
        "lassi-estimate-workload-model",
    ]
    system_prompt = (
        "You are the Planner Agent. You read the Analyst's handoff and "
        "produce a single Markdown plan that is the ONLY input the Coder "
        "Agent will see. Make it self-contained and actionable.\n\n"
        "Pipeline: context.md --(analyst)--> analysis.md --(planner)--> "
        "plan.md --(coder)--> changes.md\n\n"
        "Given an input file (analysis) and an output file path:\n"
        "1. Read the input in full.\n"
        "2. If something the Coder will need is missing, open the referenced "
        "source/build files to confirm — do not guess.\n"
        "3. Propose 1-3 concrete optimization strategies ranked by expected "
        "impact.\n"
        "4. For each strategy specify the exact file(s) to change and the "
        "concrete change shape (e.g. 'swap inner two loops in matmul()', not "
        "'improve locality').\n"
        "5. Specify the behavior to preserve and the verification focus.\n\n"
        "Do not read other LASSI/*.md files unless the analysis explicitly "
        "references them."
    )

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


class CoderAgent(Agent):
    name = "coder"
    description = (
        "Use to implement one planned LASSI optimization safely and write a "
        "change handoff."
    )
    tools = ["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-build-sanitized",
        "lassi-execute-with-latency",
    ]
    system_prompt = (
        "You are the Coder Agent. You read the Planner's plan, implement "
        "the optimizations into a designated target file, and write a single "
        "Markdown 'changes' artifact summarizing what you did.\n\n"
        "Pipeline: context.md --(analyst)--> analysis.md --(planner)--> "
        "plan.md --(coder)--> changes.md\n\n"
        "Given an input file (plan), an output file path (changes summary), "
        "a target file (the only file you may modify, already seeded with a "
        "copy of the reference) and a reference file (read-only):\n"
        "1. Read the plan in full.\n"
        "2. Read the target and the reference.\n"
        "3. Implement the planned strategies in the target file only.\n"
        "4. Compile-check before finishing. Record build commands and "
        "verification hooks in the changes artifact.\n\n"
        "If the plan is incomplete, stop and report — do not invent work. "
        "Never modify the reference file."
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
        body = _render_paths(
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


class VerifierAgent(Agent):
    name = "verifier"
    description = (
        "Use to verify LASSI candidate functional equivalence and record "
        "concrete failure evidence."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-synthesize-common-harness",
        "lassi-generate-assertion-suite",
        "lassi-run-assertion-suite",
        "lassi-run-random-equivalence-tests",
        "lassi-run-differential-fuzzer",
        "lassi-run-robustness-fuzzer",
        "lassi-compare-csv-outputs",
        "lassi-diff-csv-outputs",
        "lassi-summarize-csv",
        "lassi-synthesize-verification-report",
    ]
    system_prompt = (
        "You are the QA Verifier Agent responsible for functional "
        "equivalence and failure evidence. Use the original implementation "
        "as the oracle whenever available.\n\n"
        "Given an input file (changes/translation artifact), an output file "
        "path (verification report), a candidate source/binary, and a "
        "reference source/binary:\n"
        "1. Verify candidate behavior against the baseline with identical "
        "inputs.\n"
        "2. Prefer LASSI verification skills (assertion suite, equivalence "
        "tests, fuzzers, CSV compare) over ad-hoc scripts.\n"
        "3. Use CSV artifacts and CSV-comparison skills for numeric outputs "
        "whenever feasible.\n"
        "4. Produce concise pass/fail evidence for the next agent.\n"
        "5. On failure, preserve details in LASSI/failure_log.md."
    )

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        candidate_file: Path,
        reference_file: Path,
        notes: str = "",
    ) -> str:
        body = _render_paths(
            {
                "input file":     input_path,
                "output file":    output_path,
                "candidate file": candidate_file,
                "reference file": reference_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class ProfilerAgent(Agent):
    name = "profiler"
    description = (
        "Use for reproducible baseline benchmarking, perf counter analysis, "
        "hotspot profiling, and roofline setup for LASSI targets."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-run-benchmark",
        "lassi-collect-perf-stats",
        "lassi-profile-hotspots",
        "lassi-execute-with-profile",
        "lassi-execute-with-latency",
        "lassi-estimate-workload-model",
        "lassi-run-roofline-analysis",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
        "lassi-get-toolchain-info",
        "lassi-gprof-profiling",
    ]
    system_prompt = (
        "You are the Profiler Agent responsible for reproducible baseline "
        "performance measurement and performance-evidence collection. Do not "
        "rediscover repository structure; use the prior analysis artifacts.\n\n"
        "Given an input file (analysis / verifier-approved candidates list) "
        "and an output file path (profile summary):\n"
        "1. Measure with lassi-run-benchmark.\n"
        "2. Explain runtime with lassi-collect-perf-stats; use "
        "lassi-profile-hotspots when regressions or counter deltas require "
        "localization.\n"
        "3. Prepare roofline inputs via lassi-estimate-workload-model and "
        "lassi-run-roofline-analysis when accelerator portability or "
        "compute/memory-bound classification is requested.\n"
        "4. When multiple verified variants exist, rank them for downstream "
        "selection."
    )

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        target_binary: Path | None = None,
        notes: str = "",
    ) -> str:
        items: dict[str, Path] = {"input file": input_path, "output file": output_path}
        if target_binary is not None:
            items["target binary"] = target_binary
        body = _render_paths(items)
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class PostProfilerAgent(Agent):
    name = "post-profiler"
    description = (
        "Use to benchmark verified optimized candidates, collect perf "
        "evidence, and compare them against baseline performance artifacts."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-run-benchmark",
        "lassi-collect-perf-stats",
        "lassi-profile-hotspots",
        "lassi-execute-with-profile",
        "lassi-run-roofline-analysis",
        "lassi-compare-performance",
        "lassi-compare-roofline",
        "lassi-execute-with-latency",
        "lassi-estimate-workload-model",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
    ]
    system_prompt = (
        "You are the Post-Optimization Profiler Agent responsible for "
        "checking whether an implemented change improved performance with "
        "reproducible evidence. Reuse the baseline methodology; do not create "
        "a new benchmark unless the baseline method is unusable.\n\n"
        "Given an input file (changes artifact + baseline profile JSON) and "
        "an output file path (comparison report):\n"
        "1. Re-profile the verified candidate with the same methodology as "
        "baseline (lassi-run-benchmark, lassi-collect-perf-stats).\n"
        "2. Compare latency and perf counters against baseline using "
        "lassi-compare-performance.\n"
        "3. Use lassi-profile-hotspots and lassi-compare-roofline to explain "
        "regressions or portability shifts.\n"
        "4. Classify the optimization outcome (improved / regressed / "
        "inconclusive)."
    )

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        baseline_profile: Path,
        candidate_binary: Path,
        notes: str = "",
    ) -> str:
        body = _render_paths(
            {
                "input file":       input_path,
                "output file":      output_path,
                "baseline profile": baseline_profile,
                "candidate binary": candidate_binary,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class TranslatorAgent(Agent):
    name = "translator"
    description = (
        "Use to convert C/C++ kernels into export-friendly PyTorch "
        "translation candidates."
    )
    tools = ["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-export-model-to-pt",
    ]
    system_prompt = (
        "You are the Translator Agent responsible for converting a C/C++ "
        "kernel into export-friendly PyTorch candidates. Do not generate "
        ".pt or TOSA artifacts — that belongs to the Model Generator Agent.\n\n"
        "Given an input file (analysis + plan) and an output file path "
        "(translation notes), and the original C/C++ source files:\n"
        "1. Implement one or more semantically equivalent PyTorch "
        "candidates.\n"
        "2. Keep candidates compatible with graph export where feasible.\n"
        "3. Preserve distinct viable formulations until verification / "
        "profiling selects a winner.\n"
        "4. Check the compatibility wiki for every function/op each "
        "translation variant is expected to call during export/lowering.\n"
        "5. Leave a concise handoff (translation_notes.md, "
        "translation_variants.json) for the Verifier and Model Generator."
    )

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        source_file: Path,
        notes: str = "",
    ) -> str:
        body = _render_paths(
            {
                "input file":   input_path,
                "output file":  output_path,
                "source file":  source_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class ModelGeneratorAgent(Agent):
    name = "model-generator"
    description = (
        "Use to generate .pt, TOSA, and SODA synthesis artifacts from "
        "verified PyTorch translations."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-export-model-to-pt",
        "lassi-compile-torch-to-mlir",
        "lassi-synthesize-tosa-with-soda",
        "lassi-get-toolchain-info",
    ]
    system_prompt = (
        "You are the Model Generator Agent responsible for creating .pt, "
        "TOSA, and SODA synthesis artifacts from verified PyTorch translation "
        "candidates. Do not select an unverified candidate. Do not change "
        "semantics to force export.\n\n"
        "Given an input file (verification report + variant selection) and an "
        "output file path (model-generation notes):\n"
        "1. Generate TorchScript .pt for each verified variant in scope "
        "(lassi-export-model-to-pt).\n"
        "2. Lower each verified variant to TOSA MLIR "
        "(lassi-compile-torch-to-mlir).\n"
        "3. Run SODA synthesis from the generated TOSA output directory "
        "(lassi-synthesize-tosa-with-soda).\n"
        "4. Default to baseline synthesis (not transformed) unless the user "
        "explicitly requests transformed.\n"
        "5. Validate artifact existence, non-emptiness, basic MLIR structure, "
        "and input dependence.\n"
        "6. Record tool calls and fallback decisions concisely for "
        "reproducibility."
    )

    def build_task_prompt(
        self,
        *,
        input_path: Path,
        output_path: Path,
        variants_file: Path,
        notes: str = "",
    ) -> str:
        body = _render_paths(
            {
                "input file":    input_path,
                "output file":   output_path,
                "variants file": variants_file,
            }
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class DebuggerAgent(Agent):
    name = "debugger"
    description = (
        "Use as a last resort to investigate LASSI translation, export, or "
        "lowering workflow failures."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
        "lassi-build-sanitized",
        "lassi-execute-with-latency",
        "lassi-execute-with-profile",
        "lassi-profile-hotspots",
        "lassi-gprof-profiling",
        "lassi-collect-perf-stats",
        "lassi-summarize-csv",
        "lassi-diff-csv-outputs",
    ]
    system_prompt = (
        "You are the Debugger Agent. Investigate LASSI translation, export, "
        "or lowering workflow failures only as an absolute last resort. Do "
        "not take ownership of normal translation iteration. Do not bypass "
        "the compatibility-wiki gate.\n\n"
        "Entry gate (all must hold): (1) the flow still fails after the "
        "owning agent retried once, (2) LASSI/failure_log.md contains the "
        "concrete failing command/tool/exception, (3) the relevant "
        "ATen/PyTorch ops were checked against the compatibility wiki, "
        "(4) those entries indicate the ops should be supported.\n\n"
        "Given a failure log path, an output file path (debug report), and a "
        "dict of related artifacts:\n"
        "1. Reproduce the failure minimally.\n"
        "2. Isolate the root cause.\n"
        "3. Propose a concrete fix or hand back to the owning agent with "
        "reproducer + evidence."
    )

    def build_task_prompt(
        self,
        *,
        failure_log: Path,
        output_path: Path,
        artifacts: Mapping[str, Path] | None = None,
        notes: str = "",
    ) -> str:
        items: dict[str, Path] = {
            "failure log":   failure_log,
            "output file":   output_path,
        }
        if artifacts:
            items.update(artifacts)
        body = _render_paths(items)
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


# ---------------------------------------------------------------------------
# Orchestrators
# ---------------------------------------------------------------------------


class LassiOrchestratorAgent(Agent):
    name = "lassi-orchestrator"
    description = (
        "Use to coordinate the full LASSI optimization workflow with "
        "verification plus benchmark, perf-stat, hotspot, and roofline "
        "evidence."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
    ]
    system_prompt = (
        "You are the orchestrator for the general LASSI performance "
        "optimization workflow. You coordinate analyst -> profiler -> "
        "planner -> coder -> verifier -> post-profiler via the Task tool. "
        "You do NOT perform their work yourself.\n\n"
        "Inputs (ask the user for any missing): project folder, kernel of "
        "interest, performance-only vs energy-aware, binary equivalence vs "
        "tolerance, quantization allowed, multi-threading allowed, "
        "vectorization allowed.\n\n"
        "Workflow:\n"
        "0. Workspace setup — confirm project dir, create $PROJECT/LASSI/.\n"
        "1. Analysis — dispatch the 'analyst' subagent.\n"
        "2. Baseline profiling — dispatch the 'profiler' subagent.\n"
        "3. Planning — dispatch the 'planner' subagent.\n"
        "4. Implementation — dispatch the 'coder' subagent.\n"
        "5. Verification — dispatch the 'verifier' subagent.\n"
        "6. Final profiling — dispatch the 'post-profiler' subagent.\n\n"
        "Each subagent receives only the artifact paths it needs. Keep "
        "intermediate artifacts under $PROJECT/LASSI/."
    )

    def build_task_prompt(
        self,
        *,
        project_dir: Path,
        kernel: str,
        constraints: Mapping[str, object],
        notes: str = "",
    ) -> str:
        constraints_rendered = "\n".join(
            f"  - {k}: {v}" for k, v in constraints.items()
        )
        body = (
            f"project_dir: {project_dir}\n"
            f"kernel: {kernel}\n"
            f"constraints:\n{constraints_rendered}"
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


class TranslatorOrchestratorAgent(Agent):
    name = "translator-orchestrator"
    description = (
        "Use to coordinate C/C++ kernel to PyTorch/TOSA translation "
        "workflows with verification, benchmarking, perf evidence, and "
        "variant selection."
    )
    tools = ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Task"]
    model = "inherit"
    allowed_skills = [
        "lassi-get-toolchain-info",
        "lassi-get-machine-info",
        "lassi-get-gpu-info",
    ]
    system_prompt = (
        "You are the orchestrator for the LASSI C/C++ -> PyTorch/TOSA "
        "translation workflow. You coordinate analyst -> translator -> "
        "verifier -> profiler (for variant selection) -> model-generator -> "
        "post-profiler via the Task tool. You do NOT perform their work "
        "yourself.\n\n"
        "Inputs (ask the user for any missing): project folder, kernel of "
        "interest, performance-only vs energy-aware, binary equivalence vs "
        "tolerance, quantization allowed, multi-threading allowed, "
        "vectorization allowed.\n\n"
        "Workflow:\n"
        "0. Workspace setup — confirm project dir, create $PROJECT/LASSI/.\n"
        "1. Analysis — dispatch the 'analyst' subagent.\n"
        "2. Translation implementation — dispatch the 'translator' subagent; "
        "require it to check the compatibility wiki for each op.\n"
        "3. Verification — dispatch the 'verifier' subagent against the "
        "original C/C++ implementation as oracle.\n"
        "4. Variant selection — if multiple candidates pass, dispatch the "
        "'profiler' subagent for benchmark + perf-stat + compare; use "
        "roofline if portability or bound classification matters.\n"
        "5. Model generation — only after one verified variant is selected, "
        "dispatch the 'model-generator' subagent.\n"
        "6. Post-profiling — dispatch the 'post-profiler' subagent on the "
        "selected variant."
    )

    def build_task_prompt(
        self,
        *,
        project_dir: Path,
        kernel: str,
        constraints: Mapping[str, object],
        notes: str = "",
    ) -> str:
        constraints_rendered = "\n".join(
            f"  - {k}: {v}" for k, v in constraints.items()
        )
        body = (
            f"project_dir: {project_dir}\n"
            f"kernel: {kernel}\n"
            f"constraints:\n{constraints_rendered}"
        )
        if notes:
            body += f"\n\nAdditional notes:\n{notes}"
        return body


LASSI_AGENT_CLASSES = (
    AnalystAgent,
    LassiPlannerAgent,
    CoderAgent,
    VerifierAgent,
    ProfilerAgent,
    PostProfilerAgent,
    TranslatorAgent,
    ModelGeneratorAgent,
    DebuggerAgent,
    LassiOrchestratorAgent,
    TranslatorOrchestratorAgent,
)
"""All canonical LASSI agent classes, in roughly pipeline order."""
