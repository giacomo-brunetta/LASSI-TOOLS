# aten.ne.int_list

- Status: ❌ Unsupported
- Error: aten::ne() Expected a value of type 'List[int]' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[0.8899, 1.0966, 1.0444],         [0.0891, 0.8441, 0.6081]]) Declaration: aten::ne.int_list(int[] a, int[] b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
