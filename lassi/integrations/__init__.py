"""Wrappers for external toolchains exposed as MCP tools.

Modules:

- :mod:`lassi.integrations.export_pt` — backs ``export_model_to_pt``
  (loads a PyTorch model class and writes a ``.pt`` artifact).
- :mod:`lassi.integrations.torch_to_mlir` — backs ``compile_torch_to_mlir``
  (lowers ``.pt`` to MLIR via ``torch-mlir``).
- :mod:`lassi.integrations.toolchain_info` — backs ``get_toolchain_info``
  (reports Python, torch, torch-mlir, and LLVM versions).
- :mod:`lassi.integrations.hardware_info` — backs machine/GPU inventory tools.
- :mod:`lassi.integrations.soda` — backs SODA synthesis.
- :mod:`lassi.integrations.compatibility_resources` — backs compatibility wiki
  MCP resources.
- :mod:`lassi.integrations.torch_utils` — shared Torch input/module helpers.
"""
