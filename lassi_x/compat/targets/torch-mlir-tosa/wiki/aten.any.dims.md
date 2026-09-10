# aten.any.dims

- Status: ❌ Unsupported
- Error: aten::any() Expected a value of type 'Optional[List[int]]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::any.dims(Tensor self, int[]? dim=None, bool keepdim=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::any() Expected a value of type 'Optional[List[int]]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::any.dims(Tensor self, int[]? dim=None, bool keepdim=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dim: 1; keepdim: False
- `int32_default`: unsupported; dtype=int32; error=aten::any() Expected a value of type 'Optional[List[int]]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::any.dims(Tensor self, int[]? dim=None, bool keepdim=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dim: 1; keepdim: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
