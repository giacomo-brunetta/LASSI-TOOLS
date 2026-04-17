# aten.join

- Status: ❌ Unsupported
- Error: aten::join() Expected a value of type 'str' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.4355, -0.9983, -0.2413],         [-1.1936, -0.1575,  0.1776]]) Declaration: aten::join(str self, str[] values) -> str Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
