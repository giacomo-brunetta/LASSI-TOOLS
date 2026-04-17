# aten.hann_window.periodic

- Status: ❌ Unsupported
- Error: aten::hann_window() Expected a value of type 'int' for argument 'window_length' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.1063,  1.7462,  0.1643],         [ 0.8133, -0.7823,  0.3951]]) Declaration: aten::hann_window.periodic(int window_length, bool periodic, *, ScalarType? dtype=None, Layout? layout=None, Device? device=None, bool? pin_memory=None) -> Tensor Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
