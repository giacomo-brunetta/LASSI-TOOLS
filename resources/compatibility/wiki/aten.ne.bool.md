# aten.ne.bool

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'bool' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.8868, -0.7249, -1.0733],         [ 0.4761,  1.0694,  0.6318]]) Declaration: aten::ne.bool(bool a, bool b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
