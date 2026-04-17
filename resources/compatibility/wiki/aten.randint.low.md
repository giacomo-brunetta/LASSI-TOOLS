# aten.randint.low

- Status: ❌ Unsupported
- Error: aten::randint() Expected a value of type 'int' for argument 'low' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.6499,  1.0449, -0.0346],         [ 1.6082, -1.6651, -1.1720]]) Declaration: aten::randint.low(SymInt low, SymInt high, SymInt[] size, *, ScalarType? dtype=4, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
