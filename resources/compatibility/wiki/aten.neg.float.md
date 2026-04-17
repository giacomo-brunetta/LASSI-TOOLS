# aten.neg.float

- Status: ❌ Unsupported
- Error: aten::neg() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-2.2178,  0.8989, -1.3285],         [-0.2644,  1.1234,  0.3437]]) Declaration: aten::neg.float(float a) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
