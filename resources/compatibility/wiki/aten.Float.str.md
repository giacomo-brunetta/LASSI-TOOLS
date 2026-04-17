# aten.Float.str

- Status: ❌ Unsupported
- Error: aten::Float() Expected a value of type 'str' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.1051,  0.0385,  0.7108],         [-0.4465,  0.9974,  0.7047]]) Declaration: aten::Float.str(str a) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
