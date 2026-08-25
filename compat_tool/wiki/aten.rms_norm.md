# aten.rms_norm

- Status: ❌ Unsupported
- Error: aten::rms_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::rms_norm(Tensor input, int[] normalized_shape, Tensor? weight=None, float? eps=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::rms_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::rms_norm(Tensor input, int[] normalized_shape, Tensor? weight=None, float? eps=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=input: shape=(2, 3) dtype=float32; normalized_shape: 1; weight: shape=(2, 3) dtype=float32; eps: 1e-05
- `int32_default`: unsupported; dtype=int32; error=aten::rms_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::rms_norm(Tensor input, int[] normalized_shape, Tensor? weight=None, float? eps=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=input: shape=(2, 3) dtype=int32; normalized_shape: 1; weight: shape=(2, 3) dtype=int32; eps: 1e-05
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
