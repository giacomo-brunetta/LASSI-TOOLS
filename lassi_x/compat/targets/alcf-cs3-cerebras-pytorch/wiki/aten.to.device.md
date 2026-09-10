# aten.to.device

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; device: 'cpu'; dtype: torch.float32; non_blocking: False; copy: False; memory_format: 0 | RuntimeError: Trying to materialize a tensor outside of a step closure. All PyTorch code must be written to operate fully on torch.tensors and not call .item() (explicitly or as an implicit conversion to Python scalar), print tensor contents, or use a tensor as a Python conditional. All tensors that the system returns to PyTorch must be handled in a step closure using the @cstorch.step_closure decorator |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
