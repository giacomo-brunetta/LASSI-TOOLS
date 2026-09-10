# aten.meshgrid

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `needs_fixture` | — | RuntimeError: torch.meshgrid: Expected 0D or 1D tensor in the tensor list but got:  1.5410 -0.2935 -2.1797  0.5684 -1.0850 -1.3984 [ torch.HalfTensor{2,3} ] |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
