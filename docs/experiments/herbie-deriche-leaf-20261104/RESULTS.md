# Deriche capture with an opaque scan

The one planned candidate passed the capture/extraction gate on its first attempt.
Source is the unchanged explicit-FP64 variant from the previous trial. `_scan`
remains a runtime call, so its shape-dependent padding and loops are not traced.
Surrounding arithmetic was captured, exposing 45 supported binary64 expression
roots. Roots can overlap and are not independent repairs or validated improvements.

Two source/graph comparisons on 4x4 and 16x17 FP64 inputs matched exactly with
finite FP64 outputs. This includes partial and multiple scan panels. Four numerical
forward executions total; no original C comparison, Herbie search, accelerator,
performance or holdout qualification. Runtime loops still execute normally.

Full graph, region wrappers, source identity and comparison results:
`runs/herbie-deriche-leaf-20261104/campaign/tasks/deriche/000001/work/evidence.json`.
Frozen files and hashes: identities.json and campaign snapshots. The original
candidate and previous failed capture attempts remain untouched.

The new reusable API is `lassi_x.herbie_fx.capture_with_leaf_methods`. It copies
the model without patching the original class and is scoped to stateless helpers.
Other model control flow outside selected helpers can still block tracing. No
shape specialization was necessary for this capture. All task budgets are spent;
no remote jobs or retries are active. Next step is explicit intermediate-domain
selection and bounded Herbie searches, followed by reference validation.

Repository quality results are recorded in
`runs/herbie-deriche-leaf-20261104/quality.log`.

Final locked checks all passed: lint, formatting, strict types and tests;
603 tests passed and 3 skipped. No remote CI or hardware result is claimed.
