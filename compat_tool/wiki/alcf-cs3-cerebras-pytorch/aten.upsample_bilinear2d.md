# aten.upsample_bilinear2d

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 8, 8) dtype=float16; output_size: [8, 8]; align_corners: False; scales_h: 1.0; scales_w: 1.0 | RuntimeError: The Cerebras backend does not yet support `aten::upsample_bilinear2d(Tensor self, SymInt[2] output_size, bool align_corners, float? scales_h=None, float? scales_w=None) -> Tensor` Called with: (Half[1, 2, 8, 8], [8, 8], False, 1., 1.) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007FE6AF000FFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-linux-gnu.so  1# 0x00007FE6AF0011... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
