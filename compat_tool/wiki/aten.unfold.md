# aten.unfold

- Status: ❌ Unsupported
- Error: aten::unfold() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold(Tensor(a) self, int dimension, int size, int step) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'list'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::unfold() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold(Tensor(a) self, int dimension, int size, int step) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'list'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dimension: 1; size: [2, 3]; step: 1
- `int32_default`: unsupported; dtype=int32; error=aten::unfold() Expected a value of type 'int' for argument 'size' but instead found type 'list'. Position: 2 Value: [2, 3] Declaration: aten::unfold(Tensor(a) self, int dimension, int size, int step) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'list'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dimension: 1; size: [2, 3]; step: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
