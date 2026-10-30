# aten.upsample_nearest1d.vec

- Status: ❌ Unsupported
- Error: aten::upsample_nearest1d() Expected a value of type 'Optional[List[float]]' for argument 'scale_factors' but instead found type 'float'. Position: 2 Value: 1.0 Declaration: aten::upsample_nearest1d.vec(Tensor input, SymInt[]? output_size, float[]? scale_factors) -> Tensor Cast error details: Unable to cast Python instance of type <class 'float'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::upsample_nearest1d() Expected a value of type 'Optional[List[float]]' for argument 'scale_factors' but instead found type 'float'. Position: 2 Value: 1.0 Declaration: aten::upsample_nearest1d.vec(Tensor input, SymInt[]? output_size, float[]? scale_factors) -> Tensor Cast error details: Unable to cast Python instance of type <class 'float'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=input: shape=(2, 3) dtype=float32; output_size: [4]; scale_factors: 1.0
- `int32_default`: unsupported; dtype=int32; error=aten::upsample_nearest1d() Expected a value of type 'Optional[List[float]]' for argument 'scale_factors' but instead found type 'int'. Position: 2 Value: 1 Declaration: aten::upsample_nearest1d.vec(Tensor input, SymInt[]? output_size, float[]? scale_factors) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=input: shape=(2, 3) dtype=int32; output_size: [4]; scale_factors: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
