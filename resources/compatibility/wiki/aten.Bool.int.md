# aten.Bool.int

- Status: ❌ Unsupported
- Error: aten::Bool() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.4652, -1.1067, -1.0283],         [ 1.6218,  0.7521, -1.1415]]) Declaration: aten::Bool.int(int a) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
