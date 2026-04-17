# aten.mul.int

- Status: ❌ Unsupported
- Error: aten::mul() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[0.7722, 0.1641, 1.9818],         [0.5617, 0.0646, 0.0775]]) Declaration: aten::mul.int(int a, int b) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
