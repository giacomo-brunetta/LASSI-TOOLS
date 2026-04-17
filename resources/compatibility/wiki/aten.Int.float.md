# aten.Int.float

- Status: ❌ Unsupported
- Error: aten::Int() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.5051,  1.4509, -0.5470],         [-0.2459, -0.7678, -0.2697]]) Declaration: aten::Int.float(float a) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
