# aten.format

- Status: ❌ Unsupported
- Error: aten::format() Expected a value of type 'str' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.9788,  0.8029, -0.2611],         [-1.2822, -1.2046, -0.9339]]) Declaration: aten::format(str self, ...) -> str Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
