# Numerical accuracy policy for accelerator experiments

This policy applies to replacement experiments run after the legacy campaigns. It separates the
tight FP64 CPU translation check from accelerator error/latency measurement.

## Classification

Accelerator accuracy is classified using the worst `relative_l2` among the candidate's top-level
returned outputs. A large output therefore cannot hide an inaccurate smaller output. The aggregate
relative L2 error is retained separately as `aggregate_relative_l2` for diagnosis.

| Worst-output relative L2 | Classification | Treatment |
|---:|---|---|
| `<= 0.01` | `acceptable` | Retain and include in the error/latency frontier. |
| `> 0.01` and `< 0.10` | `concerning` | Retain, plot, and allow numerical repair. |
| `>= 0.10` | `catastrophic` | Preserve in raw records but exclude from repair and the frontier. |

Wrong shapes, non-finite values, nondeterministic output, failed execution, and violated scientific
invariants remain hard failures independently of the numerical bands. `max_abs_error` and
`max_rel_error` remain diagnostic fields; near-zero reference elements make maximum relative error
unsuitable as the rejection or optimization objective.

The CPU C-to-Torch gate still uses `arena.equivalence` in FP64. Accelerator workers always record
finite numerical output instead of applying that FP64 elementwise tolerance to FP32, FP16, or
BF16. The legacy `measure.strict_precisions` field is accepted for old configuration files but no
longer controls accelerator rejection. The default Pareto and compensation metric is now
`relative_l2`.

Every measurement records `accuracy_band`, `numerically_catastrophic`, `catastrophic_reason`, and a
derived `frontier_eligible` value. Catastrophic records are evidence and must not be deleted; they
may be shown in a separate failure panel but do not participate in the primary latency/error plot.

Thresholds are configurable under `accuracy`:

```yaml
accuracy:
  concerning_relative_l2: 0.01
  catastrophic_relative_l2: 0.10
```

Changing these thresholds defines a different experimental policy and must be reported with the
campaign configuration.
