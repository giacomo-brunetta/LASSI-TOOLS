"""Wrappers for external toolchains used by the ``lassi-*`` CLIs.

Modules:

- :mod:`lassi.integrations.export_pt` — backs ``lassi-export-model-to-pt``
  (loads a PyTorch model class and writes a ``.pt`` artifact).
- :mod:`lassi.integrations.torch_to_mlir` — backs
  ``lassi-compile-torch-to-mlir`` (lowers ``.pt`` to MLIR via ``torch-mlir``).
- :mod:`lassi.integrations.toolchain_info` — backs
  ``lassi-get-toolchain-info`` (Python / torch / torch-mlir / LLVM versions).
- :mod:`lassi.integrations.hardware_info` — backs ``lassi-get-machine-info``
  and ``lassi-get-gpu-info``.
- :mod:`lassi.integrations.soda` — backs ``lassi-synthesize-tosa-with-soda``.
- :mod:`lassi.integrations.torch_utils` — shared Torch input/module helpers.
"""
