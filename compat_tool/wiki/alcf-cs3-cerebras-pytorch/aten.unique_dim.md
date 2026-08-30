# aten.unique_dim

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; dim: 1; sorted: False; return_inverse: False; return_counts: False | RuntimeError: The Cerebras backend does not yet support `aten::unique_dim(Tensor self, int dim, bool sorted=True, bool return_inverse=False, bool return_counts=False) -> (Tensor, Tensor, Tensor)` Called with: (Half[2, 3], 1, False, False, False) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007F2E9AFFBFFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-linux-gnu.so  1# 0x00007F2E9AFFC142 ... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
