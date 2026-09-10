# Torch-MLIR to TOSA

This target treats translation to the TOSA compiler dialect as a compatibility destination in the
same registry as hardware accelerators. It does not represent NVIDIA A100 or CUDA execution.

The preserved snapshot contains 689 operator results: 213 marked supported and 476 unsupported.
It predates the current target schema, so its compiler version and Torch-MLIR revision are unknown
and its `result_format` is `flat-support`. The operator records and generated wiki pages are kept
unaltered; intermediate inventories, classifications, and old implementation code were removed.
