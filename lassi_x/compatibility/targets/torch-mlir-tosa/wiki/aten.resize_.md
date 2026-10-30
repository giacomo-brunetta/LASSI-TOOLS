# aten.resize_

- Status: ❌ Unsupported
- Error: output 1 ( 0.7242  0.8045  0.7131 -0.4810  0.0373  0.2301 [ CPUFloatType{2,3} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=output 1 ( 0.7242  0.8045  0.7131 -0.4810  0.0373  0.2301 [ CPUFloatType{2,3} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.
  spec=self: shape=(2, 3) dtype=float32; size: [2, 3]; memory_format: None
- `int32_default`: unsupported; dtype=int32; error=output 1 (-2 -1  1  3 -2 -1 [ CPUIntType{2,3} ]) of traced region did not have observable data dependence with trace inputs; this probably indicates your program cannot be understood by the tracer.
  spec=self: shape=(2, 3) dtype=int32; size: [2, 3]; memory_format: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
