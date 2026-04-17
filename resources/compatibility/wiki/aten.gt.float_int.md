# aten.gt.float_int

- Status: ❌ Unsupported
- Error: aten::gt() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-2.0097, -1.4906,  0.4432],         [-0.3114,  0.1905, -0.5845]]) Declaration: aten::gt.float_int(float a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
