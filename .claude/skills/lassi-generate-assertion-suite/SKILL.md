---
name: lassi-generate-assertion-suite
description: Generate a shared `assertion_suite.py` plus harness metadata that captures behavioral invariants between the two implementations. Use after lassi-synthesize-common-harness, before lassi-run-assertion-suite.
allowed-tools:
  - Bash(python cli/lassi-generate-assertion-suite.py*)
  - Bash(python3 cli/lassi-generate-assertion-suite.py*)
  - Read
---

Emits a runnable assertion suite anchored on shared entrypoints + I/O schemas, with optional pointers to pre-existing tests, semantic hints, and numeric tolerance.

## Invocation

```
python cli/lassi-generate-assertion-suite.py \
    --source-a SRC --source-b CAND \
    --task-type C_TO_C_OPTIMIZATION|C_TO_TORCH_TRANSLATION \
    [--entrypoints '[...]'] [--existing-tests '["t1.py"]'] \
    [--semantic-hints '["monotonic"]'] \
    [--numeric-tolerance '{"rtol":1e-5,"atol":1e-6}'] \
    [--timeout-s 120]
```

## Example

```
python cli/lassi-generate-assertion-suite.py \
    --source-a src/foo.c --source-b candidates/foo_v2.c \
    --task-type C_TO_C_OPTIMIZATION \
    --numeric-tolerance '{"rtol":1e-6,"atol":1e-9}'
```

## Underlying impl

`lassi.verification.verification_tools.generate_assertion_suite_impl`
