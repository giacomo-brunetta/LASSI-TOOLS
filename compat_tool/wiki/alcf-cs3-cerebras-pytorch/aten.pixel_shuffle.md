# aten.pixel_shuffle

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 4, 4, 4) dtype=float16; upscale_factor: 1 | RuntimeError: No input tensors found. Please make sure you are wrapping your dataloader inside a cstorch.utils.data.DataLoader.  JIT Graph:  graph():   %0 : int[] = prim::Constant[value=[1, 4, 4, 4]]()   %1 : int[] = prim::Constant[value=[1, 4, 4, 4]]()   %2 : int = prim::Constant[value=5]()   %3 : int = prim::Constant[value=0]()   %4 : Device = prim::Constant[value="lazy:0"]()   %5 : bool = prim::Constant[value=0]()   %6 : NoneType = prim::Constant()   %7 : Half(1, 4, 4, 4) = aten::empty[sou... |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
