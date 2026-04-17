# aten.neg.int

- Status: ❌ Unsupported
- Error: aten::neg() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.7338,  1.4041,  0.4978],         [-1.1584,  2.0764,  0.1691]]) Declaration: aten::neg.int(int a) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
