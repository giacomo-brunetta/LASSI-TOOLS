# aten.ge.int

- Status: ❌ Unsupported
- Error: aten::ge() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.2548, -1.0846,  0.6322],         [ 0.0980, -0.6410,  1.1349]]) Declaration: aten::ge.int(int a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
