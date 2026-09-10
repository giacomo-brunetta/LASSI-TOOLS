# aten.scaled_dot_product_attention

- Status: ❌ Unsupported
- Error: The size of tensor a (2) must match the size of tensor b (3) at non-singleton dimension 1

## Attempts

- `float32_default`: unsupported; dtype=float32; error=The size of tensor a (2) must match the size of tensor b (3) at non-singleton dimension 1
  spec=query: shape=(2, 3) dtype=float32; key: shape=(2, 3) dtype=float32; value: shape=(2, 3) dtype=float32; attn_mask: shape=(2, 3) dtype=float32; dropout_p: 1.0; is_causal: False; scale: 1.0
- `int32_default`: unsupported; dtype=int32; error=The size of tensor a (2) must match the size of tensor b (3) at non-singleton dimension 1
  spec=query: shape=(2, 3) dtype=int32; key: shape=(2, 3) dtype=int32; value: shape=(2, 3) dtype=int32; attn_mask: shape=(2, 3) dtype=int32; dropout_p: 1; is_causal: False; scale: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
