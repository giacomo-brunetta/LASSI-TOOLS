# aten.to.dtype

- Status: ❌ Unsupported
- Error: aten::to() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::to.dtype(Tensor(a) self, ScalarType dtype, bool non_blocking=False, bool copy=False, MemoryFormat? memory_format=None) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
- Alternative: Use `aten.to.other` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::to() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::to.dtype(Tensor(a) self, ScalarType dtype, bool non_blocking=False, bool copy=False, MemoryFormat? memory_format=None) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dtype: None; non_blocking: False; copy: False; memory_format: None
- `int32_default`: unsupported; dtype=int32; error=aten::to() Expected a value of type 'int' for argument 'dtype' but instead found type 'NoneType'. Position: 1 Value: None Declaration: aten::to.dtype(Tensor(a) self, ScalarType dtype, bool non_blocking=False, bool copy=False, MemoryFormat? memory_format=None) -> Tensor(a) Cast error details: Unable to cast Python instance of type <class 'NoneType'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dtype: None; non_blocking: False; copy: False; memory_format: None
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
