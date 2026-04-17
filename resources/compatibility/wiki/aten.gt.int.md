# aten.gt.int

- Status: ❌ Unsupported
- Error: aten::gt() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.3998e+00, -8.4970e-01, -4.0383e-01],         [ 9.7317e-04, -1.0274e+00,  1.1083e+00]]) Declaration: aten::gt.int(int a, int b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
