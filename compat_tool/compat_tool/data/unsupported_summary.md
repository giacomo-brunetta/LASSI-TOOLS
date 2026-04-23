# Unsupported Op Analysis

- Supported ops: 213
- Unsupported ops: 476

## Category Counts

- `backend_lowering_missing`: 228
- `constructor_or_non_tensor_input`: 5
- `harness_tracing_limitation`: 54
- `harness_wrong_inputs_or_dtype`: 93
- `language_or_runtime_helper`: 5
- `manual_review`: 80
- `non_tensor_return`: 1
- `torch_mlir_frontend_or_value_semantics_limit`: 10

## Sample Ops

### backend_lowering_missing

- `aten.acos`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.acos_`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.acosh`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.acosh_`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.adaptive_avg_pool1d`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.adaptive_avg_pool3d`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.adaptive_max_pool1d`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.adaptive_max_pool2d`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.adaptive_max_pool3d`: The op traced successfully, but torch-mlir/TOSA lowering is missing.
- `aten.alias_copy`: The op traced successfully, but torch-mlir/TOSA lowering is missing.

### constructor_or_non_tensor_input

- `aten.randint.low`: The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model.
- `aten.tensor.bool`: The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model.
- `aten.tensor.float`: The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model.
- `aten.tensor.int`: The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model.
- `aten.warn`: The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model.

### harness_tracing_limitation

- `aten.Bool.float`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.Bool.int`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.Float.Scalar`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.Int.Scalar`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.Int.bool`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.Int.float`: The test hit a tracing limitation due to non-tensor inputs or outputs.
- `aten.add.float`: The test hit a tracing limitation due to non-tensor inputs or outputs. | supported siblings: aten.add, aten.add.Scalar, aten.add.Tensor
- `aten.add.float_int`: The test hit a tracing limitation due to non-tensor inputs or outputs. | supported siblings: aten.add, aten.add.Scalar, aten.add.Tensor
- `aten.add.int`: The test hit a tracing limitation due to non-tensor inputs or outputs. | supported siblings: aten.add, aten.add.Scalar, aten.add.Tensor
- `aten.add.str`: The test hit a tracing limitation due to non-tensor inputs or outputs. | supported siblings: aten.add, aten.add.Scalar, aten.add.Tensor

### harness_wrong_inputs_or_dtype

- `aten.Bool.Tensor`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.Delete.Dict_str`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.Float.Tensor`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.Int.Tensor`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.add.t`: The harness chose the wrong input kind, shape, device, or dtype for this overload, and a sibling overload is supported. | supported siblings: aten.add, aten.add.Scalar, aten.add.Tensor
- `aten.all.bool`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.any.bool`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.any.dims`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.append.t`: The harness chose the wrong input kind, shape, device, or dtype for this op.
- `aten.as_strided`: The harness chose the wrong input kind, shape, device, or dtype for this op.

### language_or_runtime_helper

- `aten.Float.str`: This is a language/runtime helper op rather than a natural tensor compute op for TOSA.
- `aten.FloatImplicit`: This is a language/runtime helper op rather than a natural tensor compute op for TOSA.
- `aten.IntImplicit`: This is a language/runtime helper op rather than a natural tensor compute op for TOSA.
- `aten.ScalarImplicit`: This is a language/runtime helper op rather than a natural tensor compute op for TOSA.
- `aten.format`: This is a language/runtime helper op rather than a natural tensor compute op for TOSA.

### manual_review

- `aten.arange.start_out`: Needs manual inspection. | supported siblings: aten.arange, aten.arange.start, aten.arange.start_step
- `aten.batch_norm`: Needs manual inspection.
- `aten.conv_tbc`: Needs manual inspection.
- `aten.conv_tbc_backward`: Needs manual inspection.
- `aten.cosine_embedding_loss`: Needs manual inspection.
- `aten.cross_entropy_loss`: Needs manual inspection.
- `aten.diagonal_scatter`: Needs manual inspection.
- `aten.embedding`: Needs manual inspection.
- `aten.embedding_bag.padding_idx`: Needs manual inspection.
- `aten.embedding_dense_backward`: Needs manual inspection.

### non_tensor_return

- `aten.device.with_index`: The op returns a scalar or container rather than a tensor.

### torch_mlir_frontend_or_value_semantics_limit

- `aten.chunk`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.fake_quantize_per_tensor_affine_cachemask`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.nonzero_numpy`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.split.Tensor`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.split_copy.Tensor`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.tensor_split.sections`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.topk`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.triu_indices`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.unbind.int`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
- `aten.unbind_copy.int`: The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization.
