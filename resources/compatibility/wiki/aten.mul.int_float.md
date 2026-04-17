# aten.mul.int_float

- Status: ❌ Unsupported
- Error: aten::mul() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.1046,  1.4545, -1.5373],         [-1.4269, -0.8340, -0.3018]]) Declaration: aten::mul.int_float(int a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
