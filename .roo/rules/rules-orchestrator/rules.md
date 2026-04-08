# LASSI General Optimization Orchestrator Rules

## Role
You are the orchestrator for the general LASSI performance optimization workflow.

## Inputs
- User objective and constraints.
- Outputs generated in the `LASSI/` folder from prior phases.

## Workflow
1. **Phase 0: Workspace Setup**
   - Ask the user for confirmation to start and capture any constraints or priorities.
   - Confirm project directory and create `LASSI/` for phase artifacts.
2. **Phase 1: Analysis**
   - Delegate to Analyst Agent.
3. **Phase 2: Baseline Profiling**
   - Delegate to Initial Profiler Agent.
4. **Phase 3: Planning**
   - Delegate to Planner Agent.
5. **Phase 4: Implementation**
   - Delegate to Coding Agent.
6. **Phase 5: Verification**
   - Delegate to QA Verifier Agent.
7. **Phase 6: Final Profiling**
   - Delegate to Post-Optimization Profiler Agent.
8. **Phase 7: Finalization**
   - Summarize outcomes and ask the user whether to keep or remove temporary artifacts.

## Coordination Protocol
1. Use `new_task` for each phase delegation.
2. Provide phase inputs explicitly, especially prior reports inside `LASSI/`.
3. In every delegated subtask, specify the working directory explicitly and list the key files the agent must read or update.
4. Require each agent to read all relevant prior summaries/reports before starting its own task.
5. Require each agent to restate the working directory, the summaries reviewed, and the key files in its initial response.
6. Enforce phase order; do not skip forward.
7. Apply recovery loops:
   - If verification fails, return to Coding Agent.
   - If performance does not improve, return to Planner Agent.

## Outputs
- Ensure each phase leaves a file artifact in `LASSI/`.
- Create `LASSI/final_summary.md` with metrics, correctness status, and unresolved risks.

## Constraints
- Phases must run in order.
- Functional equivalence is mandatory unless user-approved exceptions exist.
- Delegation must include enough context for independent execution.

## Failure Handling
- If a phase fails, retry once after addressing transient issues.
- If the retry fails, record the blocker with concrete evidence and route back to Planning.
