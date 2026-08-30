# Target compatibility wiki generation

Compatibility is recorded per exact compiler target and declared floating-point precision. A
`compiled` result means only that the target checker compiled the named canonical operator case;
it is not a correctness, performance, or arbitrary-shape guarantee.

## Published Cerebras CS-3 result

The `alcf-cs3-cerebras-pytorch` sweep measured Cerebras PyTorch 2.10.0 and PyTorch
2.4.0+cpu against Torch-MLIR inventory revision
`874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`:

- 234 of 356 runnable FP16 canonical cases compiled (65.73%).
- 122 runnable cases were rejected by the compiler.
- 70 cases need a valid shared fixture and 11 are not applicable.
- All 437 included operators have a recorded result; there were no timeouts, compiler crashes,
  missing results, or environment errors.
- All 27 cases whose first rejection reported gRPC `UNAVAILABLE` were retried; every rejection
  reproduced and no case was promoted to compiled.

The checker used CSX `compile_only=True`, precision optimization level 1, one CSX, and one traced
data step. No wafer execution or runtime-correctness measurement was requested. The snapshot is
partial only because `needs_fixture` is not a terminal compatibility result. See the
[machine-readable snapshot](snapshots/alcf-cs3-cerebras-pytorch/snapshot.json) and
[per-operator wiki](wiki/alcf-cs3-cerebras-pytorch/).

## Published Groq result

The `groq-r01-groqflow` sweep measured GroqFlow 4.3.1 and PyTorch 2.1.0 against
Torch-MLIR inventory revision `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`:

- 200 of 356 runnable canonical cases compiled (56.18%).
- 156 runnable cases were rejected by the compiler.
- 70 cases need a valid shared fixture and 11 are not applicable.
- All 437 included operators have a recorded result; there were no timeouts, compiler crashes,
  missing results, or environment errors.

The target declares the manifest precision as `fp16`, but its checker converts floating inputs to
`float32` before GroqFlow tracing. Treat this snapshot as float32 trace evidence, not native FP16
compiler evidence. See the [machine-readable snapshot](snapshots/groq-r01-groqflow/snapshot.json)
and [per-operator wiki](wiki/groq-r01-groqflow/).

## Workflow

Prepare a canonical manifest from an exact Torch-MLIR checkout:

```bash
lassi-x-compat prepare \
  --torch-mlir-root /path/to/torch-mlir \
  --revision "$(git -C /path/to/torch-mlir rev-parse HEAD)" \
  --output /tmp/lassi-compat-manifest.json
```

The inventory admits ATen forward operations with at least one tensor input and tensor output.
Backward, in-place, and explicit `out=` overloads are excluded. Random, sparse, and quantized
operators are retained when they satisfy that contract. `pruning.yaml` holds reviewed exceptions
and requires a reason for every entry.

Copy the manifest to a target machine and run the shared probe loop there:

```bash
lassi-x-compat probe \
  --manifest /tmp/lassi-compat-manifest.json \
  --target compat_tool/targets/a100-sami-inductor.yaml \
  --run-dir compat-runs/a100 \
  --resume
```

Use `groq-r01-groqflow.yaml` inside the GroqFlow environment or
`alcf-cs3-cerebras-pytorch.yaml` on an ALCF Cerebras user node. `--op aten.mm` and `--limit N`
provide bounded smoke runs. Every compiler call runs in a subprocess and is checkpointed in
`results.json`; `--resume` reuses only terminal cells whose manifest, fixture, target, and checker
identity still match.

Publish results on the repository host:

```bash
lassi-x-compat publish \
  --manifest /tmp/lassi-compat-manifest.json \
  --results compat-runs/a100/results.json \
  --output-root compat_tool
```

The committed outputs are `snapshots/TARGET/snapshot.json` and `wiki/TARGET/*.md`. Publication
writes useful partial diagnostics but exits nonzero until every included cell is `compiled` or
`compile_rejected`.

## Result states

- `compiled`: the canonical case compiled at this target and precision.
- `compile_rejected`: a valid canonical case was rejected by the compiler.
- `not_applicable`: the operator's canonical inputs are intrinsically non-floating, so this float
  precision does not describe the case.
- `needs_fixture`: shared input generation did not produce a contract-valid eager invocation.
- `schema_mismatch`: the target's PyTorch schema cannot reconstruct the prepared case.
- `timeout`: the isolated compiler subprocess exceeded the target timeout.
- `compiler_crash`: the subprocess died or failed to return structured output.
- `environment_error`: the configured device or compiler SDK is unavailable.

The first three states are terminal. Only `compiled` is positive compatibility evidence.

## Add a target

Create a YAML file under `targets/` with `target_id`, `family`, `checker`, declared `precisions`,
`timeout_s`, `max_workers`, and vendor-specific `options`. Implement the checker as a subclass of
`CompileChecker`; only the checker may contain vendor compilation logic. Inventory, fixtures,
isolation, result schemas, resume behavior, and publishing remain shared.

Agents must select a target explicitly:

```bash
lassi-x-compat-wiki targets
lassi-x-compat-wiki op aten.mm --target TARGET --precision fp16
```

The restored flat database is exposed as `legacy-torch-mlir-tosa` with a warning until exact
replacement snapshots are published.
