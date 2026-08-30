# aten.conv_transpose3d.input

- Target: `alcf-cs3-cerebras-pytorch`
- Family: `wse`
- Compiler: `cerebras-pytorch`
- Inventory revision: `874f3a4e3cf90f54a92fe2bc1e6b8e4a5b5a1d58`

## Canonical compile cases

| Precision | Status | Input | Diagnostic |
|---|---|---|---|
| `fp16` / `canonical` | `compile_rejected` | input: shape=(1, 2, 6, 6, 6) dtype=float16; weight: shape=(2, 4, 3, 3, 3) dtype=float16; bias: None; stride: [1, 1, 1]; padding: [0]; output_padding: [0, 0, 0]; groups: 1; dilation: [1, 1, 1] | PicklableRpcError: gRPC Error:   Status Code: StatusCode.UNAVAILABLE   Details: Received http2 header with status: 502  |

> `compiled` applies only to the named case, precision, target, and compiler snapshot. It is not a runtime-correctness or performance result.
