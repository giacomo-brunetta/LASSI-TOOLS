# aten.channel_shuffle

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 4, 4, 4) dtype=float16; groups: 2 | RuntimeError: The Cerebras backend does not yet support `aten::channel_shuffle(Tensor self, SymInt groups) -> Tensor` Called with: (Half[1, 4, 4, 4], 2) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007F0EAA292FFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-linux-gnu.so  1# 0x00007F0EAA293142 in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
