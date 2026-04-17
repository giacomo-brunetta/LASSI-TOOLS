# aten.add.float

- Status: ❌ Unsupported
- Error: aten::add() Expected a value of type 'float' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.4274, -0.2425,  0.3157],         [ 0.0665,  0.3931, -0.3325]]) Declaration: aten::add.float(float a, float b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
