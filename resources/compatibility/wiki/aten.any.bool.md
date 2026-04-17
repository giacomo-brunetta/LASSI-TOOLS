# aten.any.bool

- Status: ❌ Unsupported
- Error: aten::any() Expected a value of type 'List[bool]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.0532, -0.3609,  1.8518],         [-0.0571, -1.0696, -0.7416]]) Declaration: aten::any.bool(bool[] self) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
