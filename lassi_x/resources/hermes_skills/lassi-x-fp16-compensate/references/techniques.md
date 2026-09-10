# Compensation technique reference

## Shipped helpers

`lassi_x.precision` provides FP32 accumulation, blocked-FP32 accumulation, pairwise, Kahan,
Neumaier, target-format double-word, FP32 double-word, and mode-1 stochastic-cast helpers.
Blocked-FP32 is a FABsum-style specialization: low-precision block totals are combined in FP32.
The stochastic helper acts only at explicit casts and uses ordinary PyTorch overflow behavior.

The skill's [`scripts/torch_cpu_techniques.py`](../scripts/torch_cpu_techniques.py) adds runnable
PyTorch templates for zero-centering, power-of-two scaling, equilibration, mixed refinement,
precision ramping, residual carry, Ozaki-style operand splitting, and stable reformulation, plus
wrappers for the shipped helpers. Its smoke test must execute all advertised techniques with
FP16 tensors on CPU. These examples establish PyTorch operator support; they do not establish
that a technique improves an arbitrary kernel.

## PyTorch CPU implementations

All advertised techniques passed the script's FP16 CPU checks with PyTorch 2.7.0 and 2.13.0 on
September 1, 2026. The templates use public PyTorch tensor operations and the helpers in
`lassi_x.precision`.

| Technique | Runnable template |
|---|---|
| FP32 accumulation | `fp32_accumulate` |
| Blocked-FP32/FABsum | `blocked_fp32` |
| Pairwise reduction | `pairwise` |
| Kahan summation | `kahan` |
| Neumaier summation | `neumaier` |
| Target-format double-word | `double_word` |
| FP32 double-word | `double_word_fp32` |
| Zero-centering | `zero_center_store` and `zero_center_restore` |
| Exact power-of-two scaling | `power_of_two_scaled_matmul` |
| Row/column equilibration | `equilibrated_matvec` |
| Mixed-precision iterative refinement | `mixed_refine` |
| Precision ramp | `precision_ramp` |
| Residual carry/error feedback | `residual_carry` |
| Ozaki-style operand splitting | `ozaki_split_matmul` |
| Stable reformulation | `stable_softplus` |
| Mode-1 stochastic cast | `stochastic_round` |

The refinement template intentionally uses a small Gaussian solver expressed in Torch tensor
operations. PyTorch 2.7.0 CPU does not implement `torch.linalg.solve` for FP16 or BF16, so do not
replace it with a half-precision `torch.linalg.solve` call without rechecking the target version.

Error-free transforms require round-to-nearest operations without reassociation and normally rely
on gradual underflow and no overflow. Validate the lowered backend because fusion, reassociation,
flush-to-zero, and tensor-core rounding can invalidate the source-level argument.

## Selection table

| Diagnosed mechanism | Candidate technique | Important limitation |
|---|---|---|
| Long reduction; FP32 cheap | FP32 accumulation | Accumulator and usually output are FP32 |
| Long reduction; FP32 combine affordable | Blocked-FP32/FABsum | Block size is backend- and data-dependent |
| Balanced reduction | Pairwise or superblock tree | Changes order; optimized native reduction may be better |
| Sequential mixed signs/magnitudes | Neumaier or Kahan | Compensation stored in low precision may itself be swamped |
| No wider arithmetic | Target-format multiword/double-word | More operations; strict evaluation and exponent range matter |
| Large constant plus small signal | Baseline/deviation storage or zero-centering | Baseline and reconstruction must be algebraically valid |
| Repeated discarded update | Residual carry/error feedback | Changes persistent state and needs an FP32-collapse check |
| FP16 overflow/underflow | Exact power-of-two scaling | Scaling must cover intermediates, not just inputs |
| Poor matrix range use | Row/column equilibration plus scaling | Preserve symmetry/structure and unscale the solution correctly |
| Stable convergent iteration | Precision ramp | Increase precision before rounding error reaches iteration error |
| Linear/nonlinear solve | Mixed-precision iterative refinement | Needs a meaningful higher-precision residual and convergence test |
| GEMM dominates | Ozaki/multiword operand splitting | Profitable only with suitable matrix units; may require many GEMMs |
| Unstable formula | Stable algebraic reformulation | Must still match the source contract at FP64 |
| Stagnating recurrence | Mode-1 stochastic casts | Evaluate distributions over seeds; worst-case error can be worse |

Training-only techniques such as loss scaling, FP32 master weights, and wider optimizer state are
not generic inference or scientific-kernel compensation. Use them only when the assigned program
actually performs training and the optimizer state is within scope.

## Literature anchors

- Higham and Mary survey mixed-precision refinement, block FMA, multiword arithmetic, scaling,
  and adaptive precision: <https://doi.org/10.1017/S0962492922000022>.
- Blanchard, Higham, and Mary introduce FABsum: <https://doi.org/10.1137/19M1257780>.
- Croci et al. define stochastic-rounding modes and implementation boundaries:
  <https://doi.org/10.1098/rsos.211631>.
- Ogita, Rump, and Oishi cover accurate sums and dot products with error-free transforms:
  <https://doi.org/10.1137/030601818>.
- Fasi et al. analyze multiword matrix multiplication on tensor cores:
  <https://doi.org/10.1137/21M1465032>.
