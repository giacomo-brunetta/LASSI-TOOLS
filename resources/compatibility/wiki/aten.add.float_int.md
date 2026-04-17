# aten.add.float_int

- Status: ❌ Unsupported
- Error: aten::add() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.5867, -0.9336, -0.0828],         [ 0.9039, -0.6745, -3.2835]]) Declaration: aten::add.float_int(float a, int b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
