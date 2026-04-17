# aten.pow.int_float

- Status: ❌ Unsupported
- Error: aten::pow() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.3855, -0.7922,  2.0911],         [-0.9169, -0.6037,  0.4397]]) Declaration: aten::pow.int_float(int a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
