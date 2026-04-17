# aten.add.int

- Status: ❌ Unsupported
- Error: aten::add() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.1787, -0.1826, -0.0796],         [-0.4439,  1.8370, -0.4028]]) Declaration: aten::add.int(int a, int b) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
