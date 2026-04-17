# aten.ne.int

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.2985, -0.7993,  1.4293],         [-2.1718, -0.0664,  0.2514]]) Declaration: aten::ne.int(int a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
