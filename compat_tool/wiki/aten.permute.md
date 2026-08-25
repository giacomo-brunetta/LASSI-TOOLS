# aten.permute

- Status: ❌ Unsupported
- Error: aten::permute() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::permute(Tensor(a) self, int[] dims) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::permute() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::permute(Tensor(a) self, int[] dims) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dims: 1
- `int32_default`: unsupported; dtype=int32; error=aten::permute() Expected a value of type 'List[int]' for argument 'dims' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::permute(Tensor(a) self, int[] dims) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dims: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
