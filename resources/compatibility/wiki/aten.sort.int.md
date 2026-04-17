# aten.sort.int

- Status: ❌ Unsupported
- Error: aten::sort() Expected a value of type 'List[int]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 1.7631, -1.7469, -0.0261],         [ 0.8058,  0.2333, -0.4511]]) Declaration: aten::sort.int(int[](a!) self, bool reverse=False) -> () Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
