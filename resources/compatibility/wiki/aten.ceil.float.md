# aten.ceil.float

- Status: ❌ Unsupported
- Error: aten::ceil() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.7130, -0.3792, -0.1195],         [ 0.0730, -1.2307, -0.4131]]) Declaration: aten::ceil.float(float a) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
