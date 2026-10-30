# aten.str

- Status: ❌ Unsupported
- Error: aten::str() Expected a value of type 't' for argument 'elem' but instead found type 'float'. Position: 0 Value: nan Declaration: aten::str(t elem) -> str Cast error details: toIValue() cannot handle converting to type: t

## Attempts

- `float32_default`: unsupported; dtype=float32; error=aten::str() Expected a value of type 't' for argument 'elem' but instead found type 'float'. Position: 0 Value: nan Declaration: aten::str(t elem) -> str Cast error details: toIValue() cannot handle converting to type: t
  spec=elem: nan
- `int32_default`: unsupported; dtype=int32; error=aten::str() Expected a value of type 't' for argument 'elem' but instead found type 'float'. Position: 0 Value: nan Declaration: aten::str(t elem) -> str Cast error details: toIValue() cannot handle converting to type: t
  spec=elem: nan
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
