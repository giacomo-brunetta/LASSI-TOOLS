# aten.ge.float_int

- Status: ❌ Unsupported
- Error: aten::ge() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.2771, -0.5015,  0.1069],         [ 1.0660, -0.0052, -0.2152]]) Declaration: aten::ge.float_int(float a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
