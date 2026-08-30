# aten.max_pool3d_with_indices

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | self: shape=(1, 2, 6, 6, 6) dtype=float16; kernel_size: [1, 1, 1]; stride: [1, 1, 1]; padding: [0]; dilation: [1, 1, 1]; ceil_mode: False | PicklableRpcError: gRPC Error:   Status Code: StatusCode.UNAVAILABLE   Details: Received http2 header with status: 502  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
