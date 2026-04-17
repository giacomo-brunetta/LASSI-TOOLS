# aten.device.with_index

- Status: ❌ Unsupported
- Error: aten::device() Expected a value of type 'str' for argument 'type' but instead found type 'Tensor'. Position: 0 Value: tensor([[-1.4133,  0.0554,  1.6419],         [-0.6471, -0.8085,  0.2922]]) Declaration: aten::device.with_index(str type, int index) -> Device Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
