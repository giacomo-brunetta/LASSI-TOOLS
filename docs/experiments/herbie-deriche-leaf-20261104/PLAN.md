# Deriche leaf scan capture

One unchanged explicit-FP64 candidate from runs/herbie-deriche-fp64-20261104/deriche.py.
Identity and all adapter hashes: runs/herbie-deriche-leaf-20261104/identities.json.
Locked local CPU environment as prior trial. New capture implementation treats
_scan as a runtime leaf. One campaign task, 30 seconds, one attempt, no retries,
zero model calls, Herbie searches, accelerators, C oracles, performance or holdouts.

Four numerical forwards: source and captured graph each on 4x4 and 16x17 FP64
arange(numel).reshape(shape)/numel inputs, alpha=0.25. Require exact torch.equal
and finite results; exercise padding and panel boundaries in small workloads.
Capture gate also requires at least one binary64 Herbie region. Failure preserved;
timeout/missing verdict incomplete. No numerical improvement claim. Sources
remain frozen; runtime compares transformation fidelity, not C correctness.

Frozen plan at runs/herbie-deriche-leaf-20261104/plan.yaml, campaign under campaign/.
Execute with locked lassi-x campaign prepare then run. No active remote work.
Report outcomes in RESULTS.md. Next unresolved gate is bounded Herbie search with
explicit intermediate domains and full reference validation.
