# aten.ge.float

- Status: ❌ Unsupported
- Error: aten::ge() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.7958, -0.1428, -0.5044],         [-0.0065, -1.2034,  0.0109]]) Declaration: aten::ge.float(float a, float b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
