# aten.baddbmm

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compiled` | self: shape=(2, 3, 5) dtype=float16; batch1: shape=(2, 3, 4) dtype=float16; batch2: shape=(2, 4, 5) dtype=float16; beta: 1.0; alpha: 1.0 | — |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
