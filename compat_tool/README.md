# Target compatibility wiki generation

Compatibility is recorded per exact compiler target and declared floating-point precision. A
`compiled` result means only that the target checker compiled the named canonical operator case;
it is not a correctness, performance, or arbitrary-shape guarantee.

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

Use `groq-r01-groqflow.yaml` inside the GroqFlow environment. `--op aten.mm` and `--limit N`
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
