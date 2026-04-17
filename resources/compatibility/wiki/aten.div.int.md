# aten.div.int

- Status: ❌ Unsupported
- Error: aten::div() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.7753,  0.6464,  1.0541],         [ 2.0924,  0.0511,  2.4335]]) Declaration: aten::div.int(int a, int b) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
