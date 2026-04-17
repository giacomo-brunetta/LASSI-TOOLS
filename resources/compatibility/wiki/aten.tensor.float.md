# aten.tensor.float

- Status: ❌ Unsupported
- Error: aten::tensor() Expected a value of type 'float' for argument 't' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.3157,  0.2916, -1.0291],         [ 0.4723, -0.1631, -0.1334]]) Declaration: aten::tensor.float(float t, *, ScalarType? dtype=None, Device? device=None, bool requires_grad=False) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
