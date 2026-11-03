# Selective FP32 arithmetic examples

These are patterns to adapt, not accepted repairs. Each needs a matching source,
workload, backend capability check, executed-graph audit, and accuracy result.

## FP32 reduction with low-precision storage

```python
def reduced_sum(x: torch.Tensor) -> torch.Tensor:
    # x and the returned persistent value remain FP16 or BF16.
    total32 = torch.sum(x.to(torch.float32), dim=-1)
    return total32.to(x.dtype)
```

Record the input cast, FP32 reduction and output cast. If later operators consume
`total32` directly, they are also promoted and must be recorded. The final cast
can still lose accuracy; test it rather than assuming the rescue works.

## One unstable expression in FP32

```python
def centered_second_moment(x: torch.Tensor) -> torch.Tensor:
    mean32 = x.to(torch.float32).mean(dim=0)
    centered32 = x.to(torch.float32) - mean32
    moment32 = (centered32 * centered32).mean(dim=0)
    return moment32.to(x.dtype)
```

This promotes an entire normalization expression, not just accumulation. It is
selective only if other substantial kernel work remains low precision. For a
kernel consisting solely of this expression, classify it as an FP32 fallback.

## FP32 residual with low-precision main operator

```python
def one_refinement_step(a_low: torch.Tensor, x_low: torch.Tensor,
                        b_low: torch.Tensor) -> torch.Tensor:
    # The main matrix-vector product remains low precision.
    ax_low = a_low @ x_low
    residual32 = b_low.to(torch.float32) - ax_low.to(torch.float32)
    correction_low = residual32.to(x_low.dtype)
    return x_low + correction_low
```

This illustration does not guarantee a useful refinement: the low-precision
product may already have lost the information needed for a reliable residual.
A genuine refinement should use the mathematically appropriate residual and
correction solve, with convergence and backend checks.

## Full upcast is a separate baseline

```python
def full_fp32_fallback(x: torch.Tensor, model32: torch.nn.Module) -> torch.Tensor:
    return model32(x.to(torch.float32)).to(x.dtype)
```

This is **not** MP repair. Record it as `FP32_FALLBACK` and compare its accuracy,
memory, and latency separately. A low-precision output dtype does not change the
arithmetic classification.
