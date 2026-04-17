# aten.tensor.int

- Status: ❌ Unsupported
- Error: aten::tensor() Expected a value of type 'int' for argument 't' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.5154, -1.3181,  0.9694],         [-0.1289,  0.3852,  0.5767]]) Declaration: aten::tensor.int(int t, *, ScalarType? dtype=None, Device? device=None, bool requires_grad=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
