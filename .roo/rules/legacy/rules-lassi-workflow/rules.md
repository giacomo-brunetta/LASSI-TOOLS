# LASSI Optimization Workflow (Revised)

## Global Rules

* Phases must be executed **in order**, unless an explicit failure transition redirects you.
* No phase may be skipped.
* All optimizations must preserve **functional equivalence**.
* Git operations must be **non-destructive**.
* If performance does not improve, you must re-plan and retry.
* **Environment:** All operations occur within the project folder. If the path is not provided, the agent must interrogate the user before proceeding.

---

## Phase 0: Environment Setup

**Goal:** Prepare the workspace and version control.

### Responsibilities

1. **Navigate:** `cd` to the project home directory.
2. **Branching:** Create a new branch named `agent/lassi-optimization-init`.
3. **Workspace:** Create a folder named `outputs/` at the root to store artifacts from each step.

### Completion Signal

* Announce **"Environment Ready"**

---

## Phase 1: Analyst Agent

**Goal:** Map the codebase and provide a technical specification.

### Output File Required

* `docs/lassi_analysis.md` (and a copy in `outputs/phase1_analysis.md`)

### Transition

* On success → Phase 2

---

## Phase 2: Initial Profiler (Baseline)

**Goal:** Establish the performance and energy baseline.

### Responsibilities

1. Generate GPROF data (Callgraph/Flat profile).
2. Measure Latency and Energy consumption.

### Output File Required

* `docs/lassi_baseline.md` (and a copy in `outputs/phase2_baseline.md`)

### Transition

* On success → Phase 3

---

## Phase 3: Planner Agent

**Goal:** Create a specific optimization strategy.

### Output File Required

* `docs/lassi_plan.md` (and a copy in `outputs/phase3_plan.md`)

### Transition

* On success → Phase 4

---

## Phase 4: Coding Agent (Non-Destructive)

**Goal:** Implement optimizations safely.

### Git Protocol

* Create a specific sub-branch: `agent/opt/{description}`.

### Output File Required

* A **Pull Request summary** or `outputs/phase4_changes.diff` showing the implemented code changes.

### Transition

* On success → Phase 5

---

## Phase 5: QA Verifier (Golden Master Protocol)

**Goal:** Ensure functional equivalence through strict diffing.

### Output File Required

* `outputs/phase5_verification_report.txt` (containing the results of the `diff` between `golden_output.txt` and `candidate_output.txt`).

### Decision

* **DIFF EXISTS:** Return to Phase 4.
* **IDENTICAL:** Proceed to Phase 6.

---

## Phase 6: Post-Optimization Profiler

**Goal:** Verify performance gains.

### Output File Required

* `outputs/phase6_comparison.md` (Comparison table of Baseline vs. Optimized metrics).

### Decision

* **SUCCESS:** Proceed to Cleanup.
* **FAILURE:** Return to Phase 3.

---

## Phase 7: Final Cleanup

**Goal:** Restore the repository to a clean state while preserving results.

### Responsibilities

1. **Interrogate:** Ask the user: *"Would you like me to delete the helper files (logs, temporary outputs, and golden/candidate text files) generated during this process?"*
2. **Action:** - If **Yes**: Remove the `outputs/` folder and temporary `.txt` or profile files.
* If **No**: Leave files in place and finalize the PR.



## Workflow Completion

The workflow is complete only when verification passes, performance improves, and the user has made a cleanup decision.