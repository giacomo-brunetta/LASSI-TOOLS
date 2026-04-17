# aten.ne.float_int

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.3548,  1.1945,  1.0897],         [ 0.0567, -0.3102,  0.1406]]) Declaration: aten::ne.float_int(float a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
