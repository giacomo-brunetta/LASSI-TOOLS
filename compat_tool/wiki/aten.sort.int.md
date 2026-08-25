# aten.sort.int

- Status: ❌ Unsupported
- Error: aten::sort() Expected a value of type 'List[int]' for argument 'self' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::sort.int(int[](a!) self, bool reverse=False) -> () Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::sort() Expected a value of type 'List[int]' for argument 'self' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::sort.int(int[](a!) self, bool reverse=False) -> () Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: 1; reverse: False
- `int32_default`: unsupported; dtype=int32; error=aten::sort() Expected a value of type 'List[int]' for argument 'self' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::sort.int(int[](a!) self, bool reverse=False) -> () Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: 1; reverse: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
