# aten.floordiv.int

- Status: ❌ Unsupported
- Error: aten::floordiv() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5581,  0.3324,  0.8391],         [ 1.9104,  1.4172, -0.3939]]) Declaration: aten::floordiv.int(int a, int b) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
