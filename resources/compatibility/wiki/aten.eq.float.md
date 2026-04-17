# aten.eq.float

- Status: ❌ Unsupported
- Error: aten::eq() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.2199,  1.0914, -0.6805],         [-0.8966, -1.1060,  0.0464]]) Declaration: aten::eq.float(float a, float b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
