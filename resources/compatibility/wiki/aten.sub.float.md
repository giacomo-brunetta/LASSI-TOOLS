# aten.sub.float

- Status: ❌ Unsupported
- Error: aten::sub() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5089, -0.2839, -0.5463],         [ 1.1919, -0.3295,  1.3128]]) Declaration: aten::sub.float(float a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
