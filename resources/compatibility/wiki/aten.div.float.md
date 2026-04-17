# aten.div.float

- Status: ❌ Unsupported
- Error: aten::div() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.1863,  0.5160,  0.5604],         [ 0.2026, -0.5809,  0.2282]]) Declaration: aten::div.float(float a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
