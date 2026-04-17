# aten.get.default_str

- Status: ❌ Unsupported
- Error: aten::get() Expected a value of type 'Dict[str, t]' for argument 'self' but instead found type 'Tensor'. Position: 0 Value: tensor([[-0.0245, -2.9758,  0.3292],         [-1.5613,  1.7555, -1.0447]]) Declaration: aten::get.default_str(Dict(str, t) self, str key, t default_value) -> t(*)  Python error details: ValueError: dictionary update sequence element #0 has length 3; 2 is required
