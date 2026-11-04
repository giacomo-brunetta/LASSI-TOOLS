# C adaptation → direct Tenspiler → Torch

`prepare.py OUTPUT --native-root NATIVE` prepares a two-workload ATAX development
example. See [the workflow guide](../../docs/c-to-torch.md) for commands and the
contract. Preparation makes no model calls. Configure the model before live use.
The saved replay proposal is explicitly hand-authored; it checks integration,
not model quality. The original PolyBench source stays unchanged.

Both original and adapted C must pass at MINI and SMALL before native synthesis.
Generated Torch must then pass the same original-C cases. There is no extended
operator-composition fallback. The example records an absolute system compiler
so native LLVM activation cannot accidentally change reference compilation.
