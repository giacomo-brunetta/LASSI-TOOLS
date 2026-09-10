# aten.ne.int_list

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'List[int]' for argument 'a' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::ne.int_list(int[] a, int[] b) -> bool Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
- Alternative: Use `aten.ne.Tensor` instead of this.

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::ne() Expected a value of type 'List[int]' for argument 'a' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::ne.int_list(int[] a, int[] b) -> bool Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=a: 1; b: 1
- `int32_default`: unsupported; dtype=int32; error=aten::ne() Expected a value of type 'List[int]' for argument 'a' but instead found type 'int'. Position: 0 Value: 1 Declaration: aten::ne.int_list(int[] a, int[] b) -> bool Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=a: 1; b: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
