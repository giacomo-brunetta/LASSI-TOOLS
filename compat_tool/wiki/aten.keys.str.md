# aten.keys.str

- Status: ❌ Unsupported
- Error: aten::keys() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::keys.str(Dict(str, t) self) -> str[](*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::keys() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::keys.str(Dict(str, t) self) -> str[](*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'
- `int32_default`: unsupported; dtype=int32; error=aten::keys() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::keys.str(Dict(str, t) self) -> str[](*)  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
