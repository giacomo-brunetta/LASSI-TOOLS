# aten.meshgrid.indexing

- Status: ❌ Unsupported
- Error: aten::meshgrid() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.1260, -0.3388,  0.0833],         [ 0.6997, -1.1860, -1.1896]]) Declaration: aten::meshgrid.indexing(Tensor[] tensors, *, str indexing) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::meshgrid() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.1260, -0.3388,  0.0833],         [ 0.6997, -1.1860, -1.1896]]) Declaration: aten::meshgrid.indexing(Tensor[] tensors, *, str indexing) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=tensors: shape=(2, 3) dtype=float32; indexing: 'none'
- `int32_default`: unsupported; dtype=int32; error=aten::meshgrid() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0,  0, -1],         [-3, -1, -3]], dtype=torch.int32) Declaration: aten::meshgrid.indexing(Tensor[] tensors, *, str indexing) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
  spec=tensors: shape=(2, 3) dtype=int32; indexing: 'none'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
