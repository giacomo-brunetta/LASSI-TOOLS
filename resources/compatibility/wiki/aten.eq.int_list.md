# aten.eq.int_list

- Status: ❌ Unsupported
- Error: aten::eq() Expected a value of type 'List[int]' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.4952, -0.5290, -0.1854],         [ 0.6251,  0.5003, -0.2933]]) Declaration: aten::eq.int_list(int[] a, int[] b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
