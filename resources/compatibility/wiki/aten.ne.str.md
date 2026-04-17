# aten.ne.str

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'str' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.1555,  0.6451, -1.3364],         [-0.0846,  0.4657, -0.4120]]) Declaration: aten::ne.str(str a, str b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
