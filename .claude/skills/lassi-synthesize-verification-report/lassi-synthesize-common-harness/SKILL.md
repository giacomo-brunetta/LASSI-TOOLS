---
name: lassi-synthesize-common-harness
description: Drop the shared `common_harness.py` fixture (loads either a Python module callable, a ctypes scalar shared library, or a binary-stdout target through one `run_a/run_b/compare_outputs` API) into a per-task directory, plus a metadata JSON. Use as the first step of differential verification, before lassi-generate-assertion-suite.
allowed-tools:
  - Bash(mkdir *)
  - Bash(cp *)
  - Bash(date *)
  - Write
  - Read
---

The "common harness" is a fixed Python template at `lassi/verification/common_harness_template.py`. It exposes:

- `configure(impl_a, impl_b, entrypoint="kernel", signature="double(double)")` — loads both implementations.
- `run_a(case) / run_b(case)` — call them uniformly.
- `compare_outputs(a, b, rtol=, atol=, mode="allclose"|"exact")` — numpy-aware comparison (handles torch tensors via `.detach().cpu().numpy()`).

It supports three loaders, picked by file extension:

| Suffix | Loader | Notes |
|---|---|---|
| `.py` | `importlib.util.spec_from_file_location` | `module.<entrypoint>` is called directly. |
| `.so` / `.dylib` / `.dll` | `ctypes.CDLL` | Scalar args only. Signature defaults to `"double(double)"`; supported types: `double, float, int, long`. |
| anything else | `subprocess.run` | Args are stringified onto the command line; the last numeric token of stdout is parsed back. |

## Two-step invocation

```bash
# 1. Pick a task id and create the output directory
TASK_ID="harness-$(date +%Y%m%dT%H%M%S)"
OUT=".verify/harnesses/$TASK_ID"
mkdir -p "$OUT"

# 2. Drop the template + write metadata
cp lassi/verification/common_harness_template.py "$OUT/common_harness.py"
cat > "$OUT/harness_metadata.json" <<EOF
{
  "source_a": "$(realpath src/foo.c)",
  "source_b": "$(realpath candidates/foo_v2.c)",
  "task_type": "C_TO_C_OPTIMIZATION",
  "entrypoints": [{"name": "kernel", "signature": "double(double)"}],
  "supported_interfaces": ["python_module_callable", "ctypes_scalar_shared_library"]
}
EOF
```

`task_type` is one of `C_TO_C_OPTIMIZATION` or `C_TO_TORCH_TRANSLATION`. `entrypoints[0]` is the primary one consumed by downstream tools (assertion suite, equivalence tests).

## What downstream tools expect

- `lassi-generate-assertion-suite` reads `harness_metadata.json` to know the entrypoint name/signature and writes an `assertion_suite.py` that does `import common_harness as harness`.
- `lassi-run-assertion-suite` then runs that suite with `LASSI_HARNESS_PATH=$OUT` so the import resolves.

## Notes

- The template is identical bytes every task — `cp` is correct; don't edit it per-task. If you need to change harness behavior, edit the canonical template and re-run for affected tasks.
- The metadata JSON is the only per-task customization. Keep paths absolute (`realpath`) so the suite still loads after `cd`.
- For tensor I/O (torch translations), the template's `_to_numpy` already handles `torch.Tensor` via `.detach().cpu().numpy()` — no extra setup needed.
