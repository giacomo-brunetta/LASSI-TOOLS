# aten.eye.m

- Status: ❌ Unsupported
- Error: aten::eye() Expected a value of type 'int' for argument 'n' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.4738,  0.4019,  1.5641],         [ 0.6600, -0.8082, -1.7011]]) Declaration: aten::eye.m(SymInt n, SymInt m, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
