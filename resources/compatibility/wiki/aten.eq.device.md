# aten.eq.device

- Status: ❌ Unsupported
- Error: aten::eq() Expected a value of type 'Device' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.4501,  0.5442,  1.2227],         [ 0.2901,  1.5341, -0.3536]]) Declaration: aten::eq.device(Device a, Device b) -> bool Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
