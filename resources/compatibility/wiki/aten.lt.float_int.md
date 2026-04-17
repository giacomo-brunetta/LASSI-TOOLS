# aten.lt.float_int

- Status: ❌ Unsupported
- Error: aten::lt() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.2745, -0.9553, -0.9317],         [ 0.8888,  1.5066,  0.4437]]) Declaration: aten::lt.float_int(float a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
