# aten.index_put.hacked_twin

- Status: ❌ Unsupported
- Error: aten::index_put() Expected a value of type 'List[Tensor]' for argument 'indices' but instead found type 'Tensor'. Position: 1 Value: tensor([[-3,  1,  1],         [-2, -3,  2]], dtype=torch.int32) Declaration: aten::index_put.hacked_twin(Tensor self, Tensor[] indices, Tensor values, bool accumulate=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::index_put() Expected a value of type 'List[Tensor]' for argument 'indices' but instead found type 'Tensor'. Position: 1 Value: tensor([[-3,  1,  1],         [-2, -3,  2]], dtype=torch.int32) Declaration: aten::index_put.hacked_twin(Tensor self, Tensor[] indices, Tensor values, bool accumulate=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=float32; indices: shape=(2, 3) dtype=int32; values: shape=(2, 3) dtype=float32; accumulate: False
- `int32_default`: unsupported; dtype=int32; error=aten::index_put() Expected a value of type 'List[Tensor]' for argument 'indices' but instead found type 'Tensor'. Position: 1 Value: tensor([[ 3, -3,  3],         [ 0, -3,  2]], dtype=torch.int32) Declaration: aten::index_put.hacked_twin(Tensor self, Tensor[] indices, Tensor values, bool accumulate=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=self: shape=(2, 3) dtype=int32; indices: shape=(2, 3) dtype=int32; values: shape=(2, 3) dtype=int32; accumulate: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
