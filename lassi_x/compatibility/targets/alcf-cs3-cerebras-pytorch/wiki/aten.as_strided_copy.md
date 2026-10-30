# aten.as_strided_copy

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(3, 4) dtype=float16; size: [2, 3]; stride: [3, 1]; storage_offset: 0 | ApplianceCompilationError:  WSAP011 21:54:00 GMT  Cannot compile empty CIRH module   |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
