# aten.layer_norm

- Status: ❌ Unsupported
- Error: aten::layer_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::layer_norm(Tensor input, SymInt[] normalized_shape, Tensor? weight=None, Tensor? bias=None, float eps=1.0000000000000001e-05, bool cudnn_enable=True) -> Tensor  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::layer_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::layer_norm(Tensor input, SymInt[] normalized_shape, Tensor? weight=None, Tensor? bias=None, float eps=1.0000000000000001e-05, bool cudnn_enable=True) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=input: shape=(2, 3) dtype=float32; normalized_shape: 1; weight: shape=(2, 3) dtype=float32; bias: None; eps: 1e-05; cudnn_enable: False
- `int32_default`: unsupported; dtype=int32; error=aten::layer_norm() Expected a value of type 'List[int]' for argument 'normalized_shape' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::layer_norm(Tensor input, SymInt[] normalized_shape, Tensor? weight=None, Tensor? bias=None, float eps=1.0000000000000001e-05, bool cudnn_enable=True) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=input: shape=(2, 3) dtype=int32; normalized_shape: 1; weight: shape=(2, 3) dtype=int32; bias: None; eps: 1e-05; cudnn_enable: False
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
