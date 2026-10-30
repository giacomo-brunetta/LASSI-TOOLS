# aten.Delete.Dict_str

- Status: ❌ Unsupported
- Error: aten::Delete() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::Delete.Dict_str(Dict(str, t)(a!) self, str key) -> ()  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::Delete() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::Delete.Dict_str(Dict(str, t)(a!) self, str key) -> ()  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'; key: 'none'
- `int32_default`: unsupported; dtype=int32; error=aten::Delete() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'str'. Position: 0 Value: 'none' Declaration: aten::Delete.Dict_str(Dict(str, t)(a!) self, str key) -> ()  Python error details: ValueError: dictionary update sequence element #0 has length 1; 2 is required
  spec=self: 'none'; key: 'none'
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
