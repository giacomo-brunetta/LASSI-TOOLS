# aten.clamp_max.Tensor

- Target: `graphcore-pod64-poptorch`
- Family: `ipu`
- Compiler: `poptorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float16; max: shape=(2, 3) dtype=float16 | Error: In unknown:0: 'std::exception': outputs_.size() == 1 INTERNAL ASSERT FAILED at "buildenv/lib/python3.8/site-packages/torch/include/torch/csrc/jit/ir/ir.h":510, please report a bug to PyTorch.  Exception raised from output at buildenv/lib/python3.8/site-packages/torch/include/torch/csrc/jit/ir/ir.h:510 (most recent call first): frame #0: c10::Error::Error(c10::SourceLocation, std::string) + 0x57 (0x7fd42eadfd77 in /home/gbrun/venvs/graphcore/poptorch33_compat/lib/python3.8/site-packages... |
| `fp32` / `canonical` | `compile_rejected` | self: shape=(2, 3) dtype=float32; max: shape=(2, 3) dtype=float32 | Error: In unknown:0: 'std::exception': outputs_.size() == 1 INTERNAL ASSERT FAILED at "buildenv/lib/python3.8/site-packages/torch/include/torch/csrc/jit/ir/ir.h":510, please report a bug to PyTorch.  Exception raised from output at buildenv/lib/python3.8/site-packages/torch/include/torch/csrc/jit/ir/ir.h:510 (most recent call first): frame #0: c10::Error::Error(c10::SourceLocation, std::string) + 0x57 (0x7f3477f81d77 in /home/gbrun/venvs/graphcore/poptorch33_compat/lib/python3.8/site-packages... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
