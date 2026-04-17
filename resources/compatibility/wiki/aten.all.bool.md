# aten.all.bool

- Status: ❌ Unsupported
- Error: aten::all() Expected a value of type 'List[bool]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.9267,  0.8641,  0.5545],         [ 0.1508, -0.1994, -0.6297]]) Declaration: aten::all.bool(bool[] self) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
