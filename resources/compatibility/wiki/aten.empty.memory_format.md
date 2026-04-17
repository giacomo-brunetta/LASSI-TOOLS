# aten.empty.memory_format

- Status: ❌ Unsupported
- Error: aten::empty() Expected a value of type 'List[int]' for argument 'size' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.1640,  0.3516,  0.9227],         [ 0.3776, -1.3018, -0.0960]]) Declaration: aten::empty.memory_format(SymInt[] size, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None, MemoryFormat? memory_format=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
