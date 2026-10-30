# aten.conv_transpose1d

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | input: shape=(1, 2, 8) dtype=float16; weight: shape=(2, 4, 3) dtype=float16; bias: None; stride: [1]; padding: [0]; output_padding: [0]; groups: 1; dilation: [1] | — |
| `fp32` / `canonical` | `compiled` | input: shape=(1, 2, 8) dtype=float32; weight: shape=(2, 4, 3) dtype=float32; bias: None; stride: [1]; padding: [0]; output_padding: [0]; groups: 1; dilation: [1] | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
