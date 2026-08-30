# aten.rrelu

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; lower: 1.0; upper: 1.0; training: False; generator: None | RuntimeError: The Cerebras backend does not yet support `aten::rrelu_with_noise(Tensor self, Tensor noise, Scalar lower=0.125, Scalar upper=0.33333333333333331, bool training=False, Generator? generator=None) -> Tensor` Called with: (Half[2, 3], Half[2, 3], 1., 1., False, None) Check graph dump in "ltc_unsupported.graph"  Stack Trace:   0# 0x00007F2199535FFA in /home/gbrun/R_2.10.0/venv_cerebras_pt/lib64/python3.11/site-packages/cerebras/pytorch/lib/cerebras_pytorch_lib.cpython-311-x86_64-lin... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
