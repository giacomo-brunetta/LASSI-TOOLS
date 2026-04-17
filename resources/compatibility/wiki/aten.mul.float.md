# aten.mul.float

- Status: ❌ Unsupported
- Error: aten::mul() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.4679,  0.9076,  0.0413],         [-0.9700, -0.6407, -1.4013]]) Declaration: aten::mul.float(float a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
