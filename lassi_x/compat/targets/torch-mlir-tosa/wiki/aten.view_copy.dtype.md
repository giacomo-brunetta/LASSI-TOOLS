# aten.view_copy.dtype

- Status: ❌ Unsupported
- Error: aten::view_copy() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::view_copy.dtype(Tensor self, ScalarType dtype) -> Tensor Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::view_copy() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::view_copy.dtype(Tensor self, ScalarType dtype) -> Tensor Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dtype: None
- `int32_default`: unsupported; dtype=int32; error=aten::view_copy() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::view_copy.dtype(Tensor self, ScalarType dtype) -> Tensor Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dtype: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
