# Compensation technique reference

| Failure | First choice | Important limitation |
|---|---|---|
| Reduction swamping with FP32 available | FP32 accumulation | Records accumulator/output as FP32 |
| Manual reduction without FP32 | Pairwise or FP16 double-word | Double-word is operation- and compiler-sensitive |
| Mixed signs/magnitudes | Neumaier | Sequential and expensive |
| Large constant plus small signal | Zero-centering | Requires an algebraically valid baseline |
| Overflow/underflow | Exact power-of-two scaling | Scaling and unscaling must preserve semantics |
| Iterative solver instability | Mixed-precision refinement | Requires suitable conditioning and high-precision residual |
| Long-time rounding drift | Exact stochastic rounding | Requires multiple seeds and distributional evaluation |

`lassi_x.precision` provides tested pairwise, Kahan, Neumaier, double-word, and
stochastic-cast primitives. Error-free transforms require strict evaluation; validate the
lowered backend because reassociation, fusion, or flush-to-zero may invalidate them.
