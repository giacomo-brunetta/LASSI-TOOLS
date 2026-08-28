# aten.rrelu_with_noise

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | self: shape=(2, 3) dtype=float16; noise: shape=(2, 3) dtype=float16; lower: 1.0; upper: 1.0; training: False; generator: None | — |
| `fp32` / `canonical` | `compiled` | self: shape=(2, 3) dtype=float32; noise: shape=(2, 3) dtype=float32; lower: 1.0; upper: 1.0; training: False; generator: None | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
