# aten.le.int

- Status: ❌ Unsupported
- Error: aten::le() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.9070, -2.4938,  0.5832],         [ 0.1503, -0.1167, -0.1285]]) Declaration: aten::le.int(int a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
