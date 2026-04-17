# aten.tensor.bool

- Status: ❌ Unsupported
- Error: aten::tensor() Expected a value of type 'bool' for argument 't' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.4991,  0.1765, -0.3830],         [ 2.1431,  1.6437, -0.9735]]) Declaration: aten::tensor.bool(bool t, *, ScalarType? dtype=None, Device? device=None, bool requires_grad=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
