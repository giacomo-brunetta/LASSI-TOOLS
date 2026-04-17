# aten.lt.float

- Status: ❌ Unsupported
- Error: aten::lt() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.1474,  0.5781, -0.4933],         [ 0.6862,  0.6262, -1.1393]]) Declaration: aten::lt.float(float a, float b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
