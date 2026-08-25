# aten.any.bool

- Status: ❌ Unsupported
- Error: aten::any() Expected a value of type 'List[bool]' for argument 'self' but instead found type 'bool'. Position: 0 Value: False Declaration: aten::any.bool(bool[] self) -> bool Cast error details: Unable to cast Python instance of type <class 'bool'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::any() Expected a value of type 'List[bool]' for argument 'self' but instead found type 'bool'. Position: 0 Value: False Declaration: aten::any.bool(bool[] self) -> bool Cast error details: Unable to cast Python instance of type <class 'bool'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: False
- `int32_default`: unsupported; dtype=int32; error=aten::any() Expected a value of type 'List[bool]' for argument 'self' but instead found type 'bool'. Position: 0 Value: False Declaration: aten::any.bool(bool[] self) -> bool Cast error details: Unable to cast Python instance of type <class 'bool'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
