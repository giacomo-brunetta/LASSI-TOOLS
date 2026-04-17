# aten.mul.float_int

- Status: ❌ Unsupported
- Error: aten::mul() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.0042, -0.9305, -1.3490],         [-0.0959, -1.5286,  0.0920]]) Declaration: aten::mul.float_int(float a, int b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
