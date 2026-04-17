# aten.eq.str

- Status: ❌ Unsupported
- Error: aten::eq() Expected a value of type 'str' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.0442, -0.0526, -0.2506],         [-0.5966,  0.7746, -1.0926]]) Declaration: aten::eq.str(str a, str b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
