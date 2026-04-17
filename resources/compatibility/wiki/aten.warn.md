# aten.warn

- Status: ❌ Unsupported
- Error: aten::warn() Expected a value of type 'str' for argument 'message' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.5774, -1.0347,  1.3599],         [ 0.6744, -0.4403, -0.0244]]) Declaration: aten::warn(str message, int stacklevel=2) -> () Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
