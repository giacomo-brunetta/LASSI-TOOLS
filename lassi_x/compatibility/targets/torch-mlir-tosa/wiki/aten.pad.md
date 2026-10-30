# aten.pad

- Status: ❌ Unsupported
- Error: aten::pad() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::pad(Tensor self, SymInt[] pad, str mode="constant", float? value=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::pad() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::pad(Tensor self, SymInt[] pad, str mode="constant", float? value=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=float32; pad: 1; mode: 'none'; value: 1.0
- `int32_default`: unsupported; dtype=int32; error=aten::pad() Expected a value of type 'List[int]' for argument 'pad' but instead found type 'int'. Position: 1 Value: 1 Declaration: aten::pad(Tensor self, SymInt[] pad, str mode="constant", float? value=None) -> Tensor  Python error details: TypeError: 'int' object is not iterable
  spec=self: shape=(2, 3) dtype=int32; pad: 1; mode: 'none'; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
