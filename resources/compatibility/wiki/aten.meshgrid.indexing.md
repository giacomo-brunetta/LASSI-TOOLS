# aten.meshgrid.indexing

- Status: ❌ Unsupported
- Error: aten::meshgrid() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.8774, -1.8902, -0.2617],         [-1.5143,  1.1873,  1.9406]]) Declaration: aten::meshgrid.indexing(Tensor[] tensors, *, str indexing) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
