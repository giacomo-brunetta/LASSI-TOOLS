# aten.Int.bool

- Status: ❌ Unsupported
- Error: aten::Int() Expected a value of type 'bool' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.7809, -0.4045, -0.7872],         [ 0.3364,  0.1994,  0.5920]]) Declaration: aten::Int.bool(bool a) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
