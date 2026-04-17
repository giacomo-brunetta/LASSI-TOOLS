# aten.randn.generator

- Status: ❌ Unsupported
- Error: aten::randn() Expected a value of type 'List[int]' for argument 'size' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.7706, -0.2171,  0.1163],         [ 2.6179,  0.3335,  1.0689]]) Declaration: aten::randn.generator(SymInt[] size, *, Generator? generator, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
