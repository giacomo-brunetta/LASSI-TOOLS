# aten.gt.float

- Status: ❌ Unsupported
- Error: aten::gt() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.7678, -2.0648,  0.3499],         [-0.0395,  0.0914, -0.2749]]) Declaration: aten::gt.float(float a, float b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
