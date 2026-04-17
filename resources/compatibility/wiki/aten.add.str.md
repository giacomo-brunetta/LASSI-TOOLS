# aten.add.str

- Status: ❌ Unsupported
- Error: aten::add() Expected a value of type 'str' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.7172, -1.1843,  1.7006],         [-1.1572, -0.5934,  1.4392]]) Declaration: aten::add.str(str a, str b) -> str Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
