# aten.Bool.float

- Status: ❌ Unsupported
- Error: aten::Bool() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.0480, -0.2293, -0.0965],         [ 0.6645, -0.9233, -1.3328]]) Declaration: aten::Bool.float(float a) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
