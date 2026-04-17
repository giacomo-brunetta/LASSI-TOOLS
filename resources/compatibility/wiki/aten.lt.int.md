# aten.lt.int

- Status: ❌ Unsupported
- Error: aten::lt() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.2954,  0.0822,  1.1809],         [-0.5200, -1.1428,  0.4673]]) Declaration: aten::lt.int(int a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
