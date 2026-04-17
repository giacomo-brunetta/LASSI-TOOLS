# aten.scatter_add_

- Status: ❌ Unsupported
- Error: aten::scatter_add_() Expected a value of type 'int' for argument 'dim' but instead found type 'Tensor'. Position: 1 Value: tensor([[-0.3556,  0.3877, -1.3477],         [ 1.3517, -1.0303,  0.5832]]) Declaration: aten::scatter_add_(Tensor(a!) self, int dim, Tensor index, Tensor src) -> Tensor(a!) Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
