# aten.addcdiv_

- Status: ✅ Supported
- Error: None
- Supported Profiles: float32_default
- DType Note: Supported with float32 inputs, but the int32 retry failed.

## Attempts

- `float32_default`: supported; dtype=float32; error=None
  spec=self: shape=(2, 3) dtype=float32; tensor1: shape=(2, 3) dtype=float32; tensor2: shape=(2, 3) dtype=float32; value: 1.0
- `int32_default`: unsupported; dtype=int32; error=Integer division with addcdiv is no longer supported, and in a future  release addcdiv will perform a true division of tensor1 and tensor2. The historic addcdiv behavior can be implemented as (input + value * torch.trunc(tensor1 / tensor2)).to(input.dtype) for integer inputs and as (input + value * tensor1 / tensor2) for float inputs. The future addcdiv behavior is just the latter implementation: (input + value * tensor1 / tensor2), for all dtypes.
  spec=self: shape=(2, 3) dtype=int32; tensor1: shape=(2, 3) dtype=int32; tensor2: shape=(2, 3) dtype=int32; value: 1
  note=Retried with int32 tensors to detect dtype-sensitive coverage.
