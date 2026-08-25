# aten.count_nonzero.dim_IntList

- Status: ❌ Unsupported
- Error: aten::count_nonzero() Expected a value of type 'List[int]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::count_nonzero.dim_IntList(Tensor self, int[] dim) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::count_nonzero() Expected a value of type 'List[int]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::count_nonzero.dim_IntList(Tensor self, int[] dim) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; dim: 1
- `int32_default`: unsupported; dtype=int32; error=aten::count_nonzero() Expected a value of type 'List[int]' for argument 'dim' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::count_nonzero.dim_IntList(Tensor self, int[] dim) -> Tensor Cast error details: Unable to cast Python instance of type <class 'int'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; dim: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
