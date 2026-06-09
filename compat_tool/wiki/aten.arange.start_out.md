# aten.arange.start_out

- Status: ❌ Unsupported
- Error: Unsupported kwarg-only tensor argument for aten.arange.start_out:out
- Alternative: Use `aten.arange` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=Unsupported kwarg-only tensor argument for aten.arange.start_out:out
  spec=Unavailable
- `int32_default`: unsupported; dtype=int32; error=Unsupported kwarg-only tensor argument for aten.arange.start_out:out
  spec=Unavailable
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
