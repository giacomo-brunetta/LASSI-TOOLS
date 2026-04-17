# aten.broadcast_tensors

- Status: ❌ Unsupported
- Error: aten::broadcast_tensors() Expected a value of type 'List[Tensor]' for argument 'tensors' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.5937,  1.4513, -0.4270],         [-0.7828,  0.4692, -0.9602]]) Declaration: aten::broadcast_tensors(Tensor[] tensors) -> Tensor[] Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
