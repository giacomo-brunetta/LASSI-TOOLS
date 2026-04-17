# aten.sqrt.int

- Status: ❌ Unsupported
- Error: aten::sqrt() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.6846, -0.5846, -1.2273],         [ 1.1803,  1.4455, -1.6142]]) Declaration: aten::sqrt.int(int a) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
