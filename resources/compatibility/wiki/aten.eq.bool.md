# aten.eq.bool

- Status: ❌ Unsupported
- Error: aten::eq() Expected a value of type 'bool' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.0305,  0.4769,  0.4300],         [-0.9124, -0.5242, -0.3136]]) Declaration: aten::eq.bool(bool a, bool b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
