# LASSI Translation Workflow

## Global Rules

* Phases must be executed **in order**, unless an explicit failure transition redirects you.
* No phase may be skipped.
* All optimizations must preserve **functional equivalence**.
* Git operations must be **non-destructive**.
* If performance does not improve, you must re-plan and retry.
* **Environment:** Operate inside the project folder. If not provided, interrogate the user about it.

---

## Phase 0: Environment Setup

**Goal:** Prepare the workspace and version control.

### Responsibilities

1. **Navigate:** `cd` to the project home directory.
2. **Branching:** Create a new branch named `agent/lassi-init`.
3. **Workspace:** Create a folder named `outputs/` at the root to store artifacts from each phase.

### Completion Signal

* Announce **"Environment Ready"**

---

## Phase 1: Analyst Agent

**Goal:** Map the codebase and provide a technical specification.

### Responsibilities

1. Read README files and repository structure.
2. Perform:
* Functional analysis (core purpose)
* Architecture mapping (key modules and relationships)
* Build-time configuration analysis (compile flags, parameters)
* Runtime interface analysis (CLI flags, config files)



### Output File Required

* `docs/lassi_analysis.md` (Copy to `outputs/phase1_analysis.md`)

### Transition

* On success → Phase 2

---

## Phase 2: Initial Profiler (Baseline)

**Goal:** Establish the performance and energy baseline (target to beat).

### Rules

* Prefer MCP tools and GPROF.
* Measurements must be repeatable.

### Responsibilities

1. Generate:
* GPROF callgraph and flat profile.


2. Measure:
* Latency and Energy consumption.



### Output File Required

* `docs/lassi_baseline.md` (Copy to `outputs/phase2_baseline.md`)

### Transition

* On success → Phase 3

---

## Phase 3: Planner Agent (LibTorch Translation Plan)

**Goal:** Create a translation strategy from C/C++ to **C++ LibTorch**.

### Responsibilities

1. Define translation scope (Full vs. Hot-path vs. Hybrid).
2. Map C++ structures to `at::Tensor` (layout, strides, alignment).
3. Define numeric equivalence criteria (`atol`/`rtol` for floats).
4. Define benchmarking methodology (warmup, iterations).

### Output File Required

* `docs/lassi_plan.md` (Copy to `outputs/phase3_plan.md`)

### Transition

* On success → Phase 4

---

## Phase 4: Coding Agent (Non-Destructive LibTorch Translation)

**Goal:** Implement the LibTorch translation safely.

### Git Protocol

* Create a new branch: `agent/translate/libtorch/{description}`.

### Responsibilities

1. Translate logic into **C++ LibTorch (ATen)** code.
2. Implement a test harness to build both original and LibTorch binaries.
3. Document any unavoidable numerical differences.

### Output File Required

* `outputs/phase4_changes.diff` (Summary of code changes and build instructions).

### Transition

* On success → Phase 5

---

## Phase 5: QA Verifier (Golden Master Protocol)

**Goal:** Ensure functional equivalence through strict comparison.

### Steps

1. **Baseline Run:** Build `main`  `golden_output.txt`.
2. **Candidate Run:** Build `agent/translate/...`  `candidate_output.txt`.
3. **Verification:** `diff golden_output.txt candidate_output.txt`.

### Output File Required

* `outputs/phase5_verif_report.txt` (Result of the `diff` command).

### Decision

* **DIFF EXISTS:** Return to Phase 4.
* **IDENTICAL:** Proceed to Phase 6.

---

## Phase 6: Post-Optimization Profiler

**Goal:** Verify performance gains of the LibTorch implementation.

### Responsibilities

1. Re-profile Latency and Energy using Phase 2 methodology.
2. Compare results against the baseline.

### Output File Required

* `outputs/phase6_metrics_comparison.md` (Table comparing Baseline vs. LibTorch).

### Decision

* **SUCCESS:** Proceed to Phase 7.
* **FAILURE:** Return to Phase 3.

---

## Phase 7: Cleanup & Finalization

**Goal:** Clean helper files and finalize the branch.

### Responsibilities

1. **Interrogate:** Ask the user: *"The optimization is complete. Would you like me to clean up all helper files (golden/candidate outputs, temporary profiles, and the outputs/ folder)?"*
2. **Action:** If "Yes", delete temporary artifacts. If "No", leave them for manual review.

### Workflow Completion

* Mark PR as ready for merge.