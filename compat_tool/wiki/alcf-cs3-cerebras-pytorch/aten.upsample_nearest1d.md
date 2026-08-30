# aten.upsample_nearest1d

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8) dtype=float16; output_size: [8]; scales: 1.0 | RuntimeError: The Cerebras backend does not yet support `aten::upsample_nearest1d(Tensor self, SymInt[1] output_size, float? scales=None) -> Tensor` Called with: (Half[1, 2, 8], [8], 1.) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007FEBF5316FFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-linux-gnu.so  1# 0x00007FEBF5317142 in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/s... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
