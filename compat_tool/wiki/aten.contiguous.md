# aten.contiguous

- Status: ❌ Unsupported
- Error: aten::contiguous() Expected a value of type 'int' for argument 'memory_format' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::contiguous(Tensor(a) self, *, MemoryFormat memory_format=0) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::contiguous() Expected a value of type 'int' for argument 'memory_format' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::contiguous(Tensor(a) self, *, MemoryFormat memory_format=0) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; memory_format: None
- `int32_default`: unsupported; dtype=int32; error=aten::contiguous() Expected a value of type 'int' for argument 'memory_format' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::contiguous(Tensor(a) self, *, MemoryFormat memory_format=0) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; memory_format: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
