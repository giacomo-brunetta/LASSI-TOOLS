# aten.replication_pad1d

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; padding: [1, 1] | RuntimeError: The Cerebras backend does not yet support `aten::replication_pad1d(Tensor self, SymInt[2] padding) -> Tensor` Called with: (Half[2, 3], [1, 1]) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007FA339460FFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-linux-gnu.so  1# 0x00007FA339461142 in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
