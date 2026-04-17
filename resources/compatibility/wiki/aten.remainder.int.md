# aten.remainder.int

- Status: ❌ Unsupported
- Error: aten::remainder() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.8195, -1.1491,  0.5971],         [-0.5257,  1.3660,  1.4511]]) Declaration: aten::remainder.int(int a, int b) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
