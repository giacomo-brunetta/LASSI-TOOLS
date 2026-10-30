# aten.tensor.int

- Status: ❌ Unsupported
- Error: output 1 (1 [ CPULongType{} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=output 1 (1 [ CPULongType{} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.
  spec=t: 1; dtype: None; device: 'cpu'; requires_grad: False
- `int32_default`: unsupported; dtype=int32; error=output 1 (1 [ CPULongType{} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.
  spec=t: 1; dtype: None; device: 'cpu'; requires_grad: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
