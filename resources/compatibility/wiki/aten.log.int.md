# aten.log.int

- Status: ❌ Unsupported
- Error: aten::log() Expected a value of type 'int' for argument 'a' but instead found type 'Tensor'. Position: 0 Value: tensor([[ 0.6112,  0.8162,  0.9887],         [-1.0248, -0.5996, -0.4946]]) Declaration: aten::log.int(int a) -> float Cast error details: Unable to cast Python instance of type <class 'torch.Tensor'> to C++ type '?' (#define PYBIND11_DETAILED_ERROR_MESSAGES or compile in debug mode for details)
