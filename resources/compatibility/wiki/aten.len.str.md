# aten.len.str

- Status: ❌ Unsupported
- Error: aten::len() Expected a value of type 'str' for argument 's' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.7768, -0.3445,  1.5258],         [ 0.5567,  0.1614, -0.5042]]) Declaration: aten::len.str(str s) -> int Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
