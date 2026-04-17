# aten.sub.int

- Status: ❌ Unsupported
- Error: aten::sub() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.9423,  0.5740, -0.6450],         [-0.0776, -0.4866,  1.6629]]) Declaration: aten::sub.int(int a, int b) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
