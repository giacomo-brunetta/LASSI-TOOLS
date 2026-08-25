# aten.get.default_str

- Status: ❌ Unsupported
- Error: aten::get() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::get.default_str(Dict(str, t) self, str key, t default_value) -> t(*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::get() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::get.default_str(Dict(str, t) self, str key, t default_value) -> t(*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'; key: 'none'; default_value: nan
- `int32_default`: unsupported; dtype=int32; error=aten::get() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::get.default_str(Dict(str, t) self, str key, t default_value) -> t(*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'; key: 'none'; default_value: nan
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
