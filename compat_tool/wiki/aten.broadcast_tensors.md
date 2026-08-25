# aten.broadcast_tensors

- Status: ❌ Unsupported
- Error: aten::broadcast_tensors() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.0658,  0.2825, -0.9804],         [ 1.5761, -0.6870, -0.4751]]) Declaration: aten::broadcast_tensors(Tensor[] tensors) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::broadcast_tensors() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.0658,  0.2825, -0.9804],         [ 1.5761, -0.6870, -0.4751]]) Declaration: aten::broadcast_tensors(Tensor[] tensors) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=tensors: shape=(2, 3) dtype=float32
- `int32_default`: unsupported; dtype=int32; error=aten::broadcast_tensors() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[3, 0, 0],         [3, 1, 1]], dtype=torch.int32) Declaration: aten::broadcast_tensors(Tensor[] tensors) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=tensors: shape=(2, 3) dtype=int32
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
