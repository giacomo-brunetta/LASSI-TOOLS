"""Utility helpers for the compatibility tool."""

from __future__ import annotations

import json
import logging
import math
import signal
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import torch


LOGGER = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
WIKI_DIR = PACKAGE_ROOT / "wiki"
DEFAULT_ALL_OPS_PATH = DATA_DIR / "all_ops.json"
DEFAULT_COMPATIBILITY_PATH = DATA_DIR / "compatibility.json"
DEFAULT_DB_PATH = DATA_DIR / "compat_db.json"

AttemptProfile = dict[str, Any]

RANGE_PROFILE_RULES: list[tuple[str, str, str]] = [
    ("bernoulli", "probability_[0,1]", "Tensor values must be in [0, 1]."),
    ("acos", "domain_[-1,1]", "Tensor values must be in [-1, 1]."),
    ("asin", "domain_[-1,1]", "Tensor values must be in [-1, 1]."),
    ("erfinv", "domain_[-1,1]", "Tensor values must be in [-1, 1]."),
    ("atanh", "domain_(-1,1)", "Tensor values must be in (-1, 1)."),
    ("acosh", "domain_[1,inf)", "Tensor values must be in [1, inf)."),
    ("log1p", "domain_(-1,inf)", "Tensor values must be in (-1, inf)."),
    ("log", "domain_(0,inf)", "Tensor values must be in (0, inf)."),
    ("log10", "domain_(0,inf)", "Tensor values must be in (0, inf)."),
    ("log2", "domain_(0,inf)", "Tensor values must be in (0, inf)."),
    ("sqrt", "domain_[0,inf)", "Tensor values must be in [0, inf)."),
    ("rsqrt", "domain_(0,inf)", "Tensor values must be in (0, inf)."),
    ("reciprocal", "domain_nonzero", "Tensor values must be non-zero."),
]


@dataclass
class BoundInvocation:
    """Schema-aware representation of an op invocation."""

    operator: Any
    positional_kinds: list[str]
    positional_constants: list[Any | None]
    keyword_tensor_constants: dict[str, Any]
    keyword_constants: dict[str, Any]
    tensor_specs: list[str]

    def build_module(self) -> torch.nn.Module:
        """Return a tracing module that binds constant args internally."""
        operator = self.operator
        positional_kinds = list(self.positional_kinds)
        positional_constants = list(self.positional_constants)
        keyword_tensor_constants = dict(self.keyword_tensor_constants)
        keyword_constants = dict(self.keyword_constants)

        class OpModule(torch.nn.Module):
            """Tracing wrapper that reconstructs the full operator call."""

            def forward(self, *tensor_args: Any) -> Any:
                tensor_iter = iter(tensor_args)
                full_args: list[Any] = []
                for kind, constant in zip(positional_kinds, positional_constants):
                    if kind == "tensor":
                        full_args.append(next(tensor_iter))
                    elif kind == "tensor_list":
                        full_args.append([next(tensor_iter), next(tensor_iter)])
                    else:
                        full_args.append(constant)
                return operator(*full_args, **keyword_tensor_constants, **keyword_constants)

        return OpModule().eval()


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def load_json(path: str | Path, default: Any | None = None) -> Any:
    """Load JSON from disk and return `default` if the file does not exist."""
    json_path = Path(path)
    if not json_path.exists():
        return {} if default is None else default
    with json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: str | Path, data: Any) -> None:
    """Write JSON to disk using a stable, readable format."""
    json_path = Path(path)
    ensure_directory(json_path.parent)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _sanitize_identifier(value: str) -> str:
    """Convert an op name into a Python-safe identifier suffix."""
    return "".join(character if character.isalnum() else "_" for character in value)


def _build_arg_list(op_name: str) -> list[str]:
    """Return a fallback argument variable list based on simple op heuristics."""
    if op_name.endswith(("_like", "_like.out")):
        return ["x"]
    if any(token in op_name for token in ("softmax", "log_softmax", "sum", "mean", "amax", "amin")):
        return ["x", "dim"]
    if any(token in op_name for token in ("add", "sub", "mul", "div", "maximum", "minimum", "atan2")):
        return ["x", "y"]
    if any(token in op_name for token in ("matmul", "mm", "bmm")):
        return ["x", "y"]
    if "clamp" in op_name:
        return ["x", "min_val", "max_val"]
    if any(token in op_name for token in ("cat", "stack")):
        return ["x", "y", "dim"]
    return ["x"]


def _base_name(op_name: str) -> str:
    """Return the coarse op family name used for overload grouping."""
    parts = op_name.split(".")
    return ".".join(parts[:2]) if len(parts) > 2 else op_name


def load_all_ops(path: str | Path = DEFAULT_ALL_OPS_PATH) -> dict[str, Any]:
    """Load parsed op metadata from disk."""
    return load_json(path, default={})


def resolve_torch_operator(op_name: str) -> Any:
    """Resolve a `torch.ops.aten.*` operator from its dotted name."""
    namespace = torch.ops
    for piece in op_name.split("."):
        namespace = getattr(namespace, piece)
    return namespace


def resolve_torch_schema(op_name: str, operator: Any | None = None) -> Any:
    """Resolve the torch FunctionSchema for an aten op."""
    if operator is None:
        operator = resolve_torch_operator(op_name)
    schema = getattr(operator, "_schema", None)
    if schema is not None:
        return schema
    schemas = getattr(operator, "_schemas", None)
    if isinstance(schemas, dict):
        if "" in schemas:
            return schemas[""]
        return next(iter(schemas.values()))
    raise ValueError(f"Could not resolve schema for {op_name}")


def generate_test_function(op_name: str) -> str:
    """
    Return Python source code for a minimal test function using the op.

    The generated source defines a function named `test_<sanitized op name>`.
    """
    arg_list = _build_arg_list(op_name)
    function_name = f"test_{_sanitize_identifier(op_name)}"
    op_expr = op_name.split(".", maxsplit=1)[1] if "." in op_name else op_name

    body = [
        "import torch",
        "",
        f"def {function_name}({', '.join(arg_list)}):",
    ]

    if arg_list == ["x"]:
        body.append(f"    return torch.ops.aten.{op_expr}(x)")
    elif arg_list == ["x", "dim"]:
        body.append(f"    return torch.ops.aten.{op_expr}(x, dim)")
    elif arg_list == ["x", "y"]:
        body.append(f"    return torch.ops.aten.{op_expr}(x, y)")
    elif arg_list == ["x", "min_val", "max_val"]:
        body.append(f"    return torch.ops.aten.{op_expr}(x, min_val, max_val)")
    elif arg_list == ["x", "y", "dim"]:
        body.append(f"    return torch.ops.aten.{op_expr}([x, y], dim)")
    else:
        body.append(f"    return torch.ops.aten.{op_expr}({', '.join(arg_list)})")

    return "\n".join(body) + "\n"


def _make_tensor(shape: tuple[int, ...], *, dtype: torch.dtype, mode: str = "default") -> torch.Tensor:
    """Create a tensor for a specific dtype and value-domain mode."""
    if dtype in (torch.int32, torch.int64, torch.int16, torch.int8, torch.uint8, torch.bool):
        if mode == "probability_[0,1]":
            return torch.randint(0, 2, shape, dtype=torch.int64).to(dtype)
        if mode == "domain_[1,inf)":
            return torch.randint(1, 5, shape, dtype=torch.int64).to(dtype)
        if mode == "domain_nonzero":
            return torch.randint(1, 5, shape, dtype=torch.int64).to(dtype)
        if mode == "domain_[-1,1]":
            return torch.randint(-1, 2, shape, dtype=torch.int64).to(dtype)
        return torch.randint(-3, 4, shape, dtype=torch.int64).to(dtype)

    if mode == "probability_[0,1]":
        return torch.rand(shape, dtype=dtype)
    if mode == "domain_[-1,1]":
        return (torch.rand(shape, dtype=dtype) * 2.0) - 1.0
    if mode == "domain_(-1,1)":
        return (torch.rand(shape, dtype=dtype) * 1.8) - 0.9
    if mode == "domain_[1,inf)":
        return torch.rand(shape, dtype=dtype) + 1.0
    if mode == "domain_(0,inf)":
        return torch.rand(shape, dtype=dtype) + 0.1
    if mode == "domain_(-1,inf)":
        return torch.rand(shape, dtype=dtype) + 0.1
    if mode == "domain_[0,inf)":
        return torch.rand(shape, dtype=dtype)
    if mode == "domain_nonzero":
        return torch.rand(shape, dtype=dtype) + 0.1
    return torch.randn(shape, dtype=dtype)


def _preferred_tensor_dtype(op_name: str, arg_name: str, arg_type: str, requested_dtype: torch.dtype) -> torch.dtype:
    """Return a more appropriate tensor dtype for families with specific requirements."""
    lowered_name = op_name.lower()
    lowered_arg = arg_name.lower()
    if any(token in lowered_name for token in ("bitwise_", "bincount", "bucketize")):
        return torch.int64
    if any(token in lowered_name for token in ("index.", "index_put", "index_select", "gather", "narrow.tensor")) and lowered_arg in (
        "index",
        "indices",
        "start",
    ):
        return torch.int64
    if any(token in lowered_name for token in ("imag", "view_as_real")):
        return torch.complex64
    if "view_as_complex" in lowered_name:
        return torch.float32
    if "one_hot" in lowered_name:
        return torch.int64
    if "cross_entropy_loss" in lowered_name and lowered_arg == "target":
        return torch.int64
    if "embedding_bag" in lowered_name and lowered_arg in ("indices", "offsets"):
        return torch.int64
    if "embedding" in lowered_name and lowered_arg == "indices":
        return torch.int64
    if lowered_arg in ("index", "indices"):
        return torch.int64
    if lowered_arg in ("mask", "condition"):
        return torch.bool
    if "bucketize" in lowered_name and lowered_arg == "boundaries":
        return torch.float32
    if "quantized" in lowered_name or "int_repr" in lowered_name:
        return torch.quint8
    return requested_dtype


def _shape_for_tensor_arg(op_name: str, arg_name: str, arg_index: int) -> tuple[int, ...]:
    """Choose a schema-aware tensor shape for a given op argument."""
    family = _base_name(op_name)
    lowered_arg = arg_name.lower()

    if family in {"aten.Bool.Tensor", "aten.Float.Tensor", "aten.Int.Tensor", "aten.item"}:
        return ()
    if "conv_tbc" in family:
        if lowered_arg in ("self", "input"):
            return (5, 2, 3)
        if lowered_arg == "weight":
            return (3, 3, 3)
        return (3,)
    if family == "aten.convolution":
        if lowered_arg == "input":
            return (1, 2, 8, 8)
        if lowered_arg == "weight":
            return (4, 2, 3, 3)
        return (4,)
    if family == "aten.convolution_backward":
        if lowered_arg == "grad_output":
            return (1, 4, 6, 6)
        if lowered_arg == "input":
            return (1, 2, 8, 8)
        if lowered_arg == "weight":
            return (4, 2, 3, 3)
        return (4,)
    if "conv_transpose1d" in family:
        return (1, 2, 8) if lowered_arg in ("input", "self") else (2, 4, 3)
    if "conv_transpose2d" in family:
        return (1, 2, 8, 8) if lowered_arg in ("input", "self") else (2, 4, 3, 3)
    if "conv_transpose3d" in family:
        return (1, 2, 6, 6, 6) if lowered_arg in ("input", "self") else (2, 4, 3, 3, 3)
    if "conv1d" in family:
        return (1, 2, 8) if lowered_arg in ("input", "self") else (4, 2, 3)
    if "conv2d" in family:
        return (1, 2, 8, 8) if lowered_arg in ("input", "self") else (4, 2, 3, 3)
    if "conv3d" in family:
        return (1, 2, 6, 6, 6) if lowered_arg in ("input", "self") else (4, 2, 3, 3, 3)
    if "pool1d" in family:
        return (1, 2, 8)
    if "pool2d" in family:
        return (1, 2, 8, 8)
    if "pool3d" in family:
        return (1, 2, 6, 6, 6)
    if "upsample_nearest1d" in family:
        return (1, 2, 8)
    if "upsample" in family:
        return (1, 2, 8, 8)
    if "baddbmm" in family:
        if lowered_arg == "self":
            return (2, 3, 5)
        if lowered_arg == "batch1":
            return (2, 3, 4)
        return (2, 4, 5)
    if "batch_norm" in family:
        if lowered_arg == "input":
            return (2, 3, 4, 4)
        if lowered_arg in ("weight", "bias", "running_mean", "running_var", "save_mean", "save_invstd"):
            return (3,)
    if "group_norm" in family or "native_group_norm" in family:
        if lowered_arg in ("input", "grad_out"):
            return (2, 3, 4, 4)
        if lowered_arg in ("weight", "bias", "mean", "rstd"):
            return (3,)
    if "instance_norm" in family:
        if lowered_arg == "input":
            return (2, 3, 4, 4)
        if lowered_arg in ("weight", "bias", "running_mean", "running_var", "save_mean", "save_var"):
            return (3,)
    if "layer_norm" in family or "native_layer_norm" in family or "rms_norm" in family:
        if lowered_arg in ("weight", "bias"):
            return (3,)
    if "channel_shuffle" in family:
        return (1, 4, 4, 4)
    if "pixel_shuffle" in family or "pixel_unshuffle" in family:
        return (1, 4, 4, 4)
    if "bmm" in family:
        if lowered_arg in ("self", "batch1"):
            return (2, 3, 4)
        return (2, 4, 5)
    if "addmm" in family:
        if lowered_arg == "self":
            return (2, 3)
        if lowered_arg == "mat1":
            return (2, 4)
        return (4, 3)
    if any(token in family for token in ("matmul", ".mm", "linalg_det", "linalg_slogdet")):
        if "linalg_det" in family or "linalg_slogdet" in family:
            return (3, 3)
        if lowered_arg in ("self", "mat1"):
            return (2, 4)
        return (4, 3)
    if family == "aten.mv":
        return (2, 3) if lowered_arg in ("self", "mat") else (3,)
    if family == "aten.outer" or family == "aten.dot":
        return (4,)
    if "glu" in family:
        return (2, 4)
    if "view_as_complex" in family:
        return (2, 3, 2)
    if "view_as_real" in family or "imag" in family:
        return (2, 3)
    if family in {"aten.as_strided", "aten.as_strided_copy", "aten.as_strided_scatter"}:
        return (3, 4)
    if "one_hot" in family:
        return (2, 3)
    if family == "aten.embedding" and lowered_arg == "weight":
        return (4, 3)
    if family == "aten.embedding_bag" and lowered_arg == "weight":
        return (4, 3)
    if family == "aten.embedding_dense_backward":
        if lowered_arg == "grad_output":
            return (2, 3, 3)
        if lowered_arg == "indices":
            return (2, 3)
    if family == "aten.cross_entropy_loss" and lowered_arg == "weight":
        return (3,)
    if family in {"aten.fill.Tensor", "aten.fill_.Tensor", "aten.masked_fill.Tensor", "aten.masked_fill_.Tensor"} and lowered_arg == "value":
        return ()
    if family == "aten.diagonal_scatter" and lowered_arg == "src":
        return (2,)
    if family == "aten.gather" and lowered_arg == "index":
        return (2, 3)
    if family == "aten.grid_sampler":
        if lowered_arg == "input":
            return (1, 2, 4, 4)
        if lowered_arg == "grid":
            return (1, 4, 4, 2)
    if family == "aten.im2col":
        return (1, 2, 4, 4)
    if family == "aten.index_select" and lowered_arg == "index":
        return (2,)
    if family == "aten.narrow.Tensor" and lowered_arg == "start":
        return ()
    if family == "aten.fake_quantize_per_tensor_affine.tensor_qparams" and lowered_arg in ("scale", "zero_point"):
        return ()
    if "bucketize" in family and lowered_arg == "boundaries":
        return (4,)
    if "embedding_bag" in family and lowered_arg == "indices":
        return (4,)
    if "embedding_bag" in family and lowered_arg == "offsets":
        return (2,)
    if "embedding" in family and lowered_arg == "indices":
        return (2, 3)
    if "cross_entropy_loss" in family and lowered_arg == "target":
        return (2,)
    if "cosine_embedding_loss" in family and lowered_arg == "target":
        return (2,)
    if "fake_quantize_per_channel_affine" in family and lowered_arg in ("scale", "zero_point"):
        return (3,)
    if "bernoulli" in family:
        return (2, 3)
    return (2, 3)


def _make_quantized_tensor(shape: tuple[int, ...]) -> torch.Tensor:
    """Create a simple quantized tensor."""
    base = torch.randint(0, 16, shape, dtype=torch.uint8)
    return torch.quantize_per_tensor(base.float(), scale=0.1, zero_point=0, dtype=torch.quint8)


def _make_tensor_arg(
    op_name: str,
    arg_name: str,
    arg_type: str,
    arg_index: int,
    requested_dtype: torch.dtype,
    tensor_mode: str,
) -> torch.Tensor:
    """Create a schema-aware tensor argument."""
    dtype = _preferred_tensor_dtype(op_name, arg_name, arg_type, requested_dtype)
    shape = _shape_for_tensor_arg(op_name, arg_name, arg_index)

    if dtype == torch.quint8:
        return _make_quantized_tensor(shape)
    if dtype == torch.bool:
        return torch.randint(0, 2, shape, dtype=torch.int64).to(torch.bool)

    tensor = _make_tensor(shape, dtype=dtype, mode=tensor_mode)
    family = _base_name(op_name)
    lowered_arg = arg_name.lower()

    if family in {"aten.Bool.Tensor", "aten.Float.Tensor", "aten.Int.Tensor", "aten.item"}:
        return torch.tensor(1.0, dtype=torch.float32)
    if "embedding" in family and lowered_arg == "indices":
        return torch.randint(0, 4, shape, dtype=torch.int64)
    if family == "aten.embedding" and lowered_arg == "weight":
        return torch.randn(shape, dtype=torch.float32)
    if "embedding_bag" in family and lowered_arg == "indices":
        return torch.randint(0, 4, shape, dtype=torch.int64)
    if "embedding_bag" in family and lowered_arg == "offsets":
        return torch.tensor([0, 2], dtype=torch.int64)
    if family == "aten.embedding_bag" and lowered_arg == "weight":
        return torch.randn(shape, dtype=torch.float32)
    if family == "aten.embedding_dense_backward" and lowered_arg == "indices":
        return torch.randint(0, 4, shape, dtype=torch.int64)
    if "one_hot" in family:
        return torch.randint(0, 4, shape, dtype=torch.int64)
    if "cross_entropy_loss" in family and lowered_arg == "target":
        return torch.randint(0, 3, shape, dtype=torch.int64)
    if "cosine_embedding_loss" in family and lowered_arg == "target":
        return torch.randint(0, 2, shape, dtype=torch.int64) * 2 - 1
    if family in {"aten.fill.Tensor", "aten.fill_.Tensor", "aten.masked_fill.Tensor", "aten.masked_fill_.Tensor"} and lowered_arg == "value":
        return torch.tensor(1.0, dtype=torch.float32)
    if family == "aten.gather" and lowered_arg == "index":
        return torch.tensor([[0, 1, 2], [0, 1, 2]], dtype=torch.int64)
    if family == "aten.index_select" and lowered_arg == "index":
        return torch.tensor([0, 1], dtype=torch.int64)
    if family == "aten.narrow.Tensor" and lowered_arg == "start":
        return torch.tensor(0, dtype=torch.int64)
    if family in {"aten.index.Tensor_hacked_twin", "aten.index_put.hacked_twin", "aten.index_put_.hacked_twin"} and lowered_arg.startswith("indices_"):
        return torch.tensor([0, 1], dtype=torch.int64)
    if family == "aten.fake_quantize_per_tensor_affine.tensor_qparams":
        if lowered_arg == "scale":
            return torch.tensor(0.1, dtype=torch.float32)
        if lowered_arg == "zero_point":
            return torch.tensor(0, dtype=torch.int32)
    if "bucketize" in family and lowered_arg == "boundaries":
        return torch.tensor([0.0, 1.0, 2.0, 3.0], dtype=torch.float32)
    if "binary_cross_entropy" in family and lowered_arg in ("self", "target"):
        return torch.rand(shape, dtype=torch.float32)
    if "fake_quantize_per_channel_affine" in family and lowered_arg == "scale":
        return torch.rand(shape, dtype=torch.float32) + 0.1
    if "fake_quantize_per_channel_affine" in family and lowered_arg == "zero_point":
        return torch.zeros(shape, dtype=torch.int32)
    if "view_as_real" in family or "imag" in family:
        return torch.randn(shape, dtype=torch.complex64)
    return tensor


def _constant_from_type(op_name: str, arg_name: str, arg_type: str, requested_dtype: torch.dtype) -> Any:
    """Generate a constant argument for non-tensor schema entries."""
    lowered_type = arg_type.lower()
    lowered_name = arg_name.lower()
    family = _base_name(op_name)

    if "optional" in lowered_type and any(token in lowered_name for token in ("bias", "generator")):
        return None
    if family in {"aten.as_strided", "aten.as_strided_copy", "aten.as_strided_scatter"}:
        if lowered_name == "size":
            return [2, 3]
        if lowered_name == "stride":
            return [3, 1]
        if lowered_name == "storage_offset":
            return 0
    if lowered_name in ("dim", "axis"):
        return [1] if "list[" in lowered_type else 1
    if lowered_name == "keepdim":
        return False
    if lowered_name == "groups":
        return 2 if "channel_shuffle" in family else 1
    if lowered_name == "padding_idx":
        return -1
    if lowered_name == "num_classes":
        return 4
    if lowered_name == "num_weights":
        return 4
    if lowered_name == "scale_grad_by_freq":
        return False
    if lowered_name == "training":
        return False
    if lowered_name == "norm":
        return "backward"
    if lowered_name == "eps":
        return 1e-5
    if lowered_name == "ignore_index":
        return -100
    if lowered_name == "reduction":
        return 1
    if lowered_name == "dim1":
        return 0
    if lowered_name == "dim2":
        return 1
    if lowered_name == "diagonal":
        return 0
    if lowered_name == "rounding_mode":
        return "trunc"
    if lowered_name == "mode":
        if family == "aten.pad":
            return "constant"
        if "linalg_qr" in family:
            return "reduced"
        if "embedding_bag" in family:
            return 0
        return "none"
    if lowered_name == "padding":
        if family == "aten.constant_pad_nd":
            return [1, 1]
        if family == "aten.pad":
            return "constant"
        if "conv" in family and "padding" in op_name:
            return "same"
        if "reflection_pad1d" in family or "replication_pad1d" in family:
            return [1, 1]
        if "reflection_pad2d" in family or "replication_pad2d" in family:
            return [1, 1, 1, 1]
        if "reflection_pad3d" in family or "replication_pad3d" in family:
            return [1, 1, 1, 1, 1, 1]
        return [0]
    if lowered_name == "output_size":
        if family == "aten.col2im":
            return [4, 4]
        if "upsample_nearest1d" in family:
            return [8]
        if "upsample" in family:
            return [8, 8]
        if "1d" in family:
            return [4]
        if "2d" in family:
            return [4, 4]
        if "3d" in family:
            return [4, 4, 4]
    if lowered_name in ("stride", "dilation", "kernel_size"):
        if family in {"aten.im2col", "aten.col2im"}:
            return [2, 2] if lowered_name == "kernel_size" else [1, 1]
        if "1d" in family:
            return [1]
        if "2d" in family:
            return [1, 1]
        if "3d" in family:
            return [1, 1, 1]
    if lowered_name == "output_padding":
        if "1d" in family:
            return [0]
        if "2d" in family:
            return [0, 0]
        if "3d" in family:
            return [0, 0, 0]
    if lowered_name in ("size", "shape"):
        return [2, 3]
    if lowered_name == "normalized_shape":
        return [3]
    if lowered_name == "output_mask":
        return [True, True, True]
    if lowered_name == "bias_sizes" and family == "aten.convolution_backward":
        return [4]
    if lowered_name == "repeats":
        return [1, 1]
    if lowered_name == "dims":
        return [0, 1]
    if lowered_name == "split_sizes":
        return [1, 2]
    if lowered_name == "split_size":
        return [1, 2] if "list[" in lowered_type else 1
    if lowered_name == "shifts":
        return [1]
    if lowered_name == "scale_factors":
        return [1.0, 1.0]
    if lowered_name == "window":
        return None
    if lowered_name == "hop_length":
        return 1
    if lowered_name == "win_length":
        return 2
    if lowered_name == "n_fft":
        return 2
    if lowered_name == "onesided":
        return False
    if lowered_name == "return_complex":
        return False
    if lowered_name == "requires_grad":
        return False
    if lowered_name == "device":
        return "cpu"
    if lowered_name == "layout":
        return None
    if lowered_name == "memory_format":
        return 0
    if lowered_name == "dtype":
        return torch.int32 if requested_dtype == torch.int32 else torch.float32
    if lowered_name == "equation" and family == "aten.einsum":
        return "ij,jk->ik"
    if lowered_name == "path" and family == "aten.einsum":
        return None
    if lowered_name == "ord":
        return 2.0
    if lowered_name == "cudnn_enable":
        return False
    if lowered_name == "right":
        return False
    if lowered_name == "out_int32":
        return False
    if lowered_name == "quant_min":
        return 0
    if lowered_name == "quant_max":
        return 255

    if "list[int]" in lowered_type or "optional[list[int]]" in lowered_type or "int[]" in lowered_type:
        if "1d" in family:
            return [1]
        if "2d" in family:
            return [1, 1]
        if "3d" in family:
            return [1, 1, 1]
        return [1]
    if "list[bool]" in lowered_type or "optional[list[bool]]" in lowered_type:
        return [True]
    if "list[float]" in lowered_type or "optional[list[float]]" in lowered_type:
        return [1.0]
    if "list[tensor]" in lowered_type or "optional[list[tensor]]" in lowered_type:
        return None
    if "list[" in lowered_type:
        return [1]
    if "bool" in lowered_type:
        return False
    if "number" in lowered_type:
        return 1 if requested_dtype == torch.int32 else 1.0
    if "float" in lowered_type or "scalar" in lowered_type:
        return 1 if requested_dtype == torch.int32 else 1.0
    if lowered_type == "int":
        return 1
    if "string" in lowered_type or "str" in lowered_type:
        return "same" if "padding" in lowered_name else "none"
    if "device" in lowered_type:
        return "cpu"
    if "generator" in lowered_type:
        return None
    if "optional" in lowered_type:
        return None
    return python_default_for_type(arg_type)


def get_range_profile(op_name: str) -> AttemptProfile | None:
    """Return a range-restricted float profile for ops with known numeric domains."""
    family = _base_name(op_name)
    for token, mode, note in RANGE_PROFILE_RULES:
        if token in family:
            return {
                "name": f"float32_{mode}",
                "tensor_dtype": torch.float32,
                "tensor_mode": mode,
                "range_note": note,
            }
    return None


def build_attempt_profiles(op_name: str) -> list[AttemptProfile]:
    """Return the ordered list of analysis profiles to try for an op."""
    profiles: list[AttemptProfile] = [
        {
            "name": "float32_default",
            "tensor_dtype": torch.float32,
            "tensor_mode": "default",
            "range_note": None,
        },
        {
            "name": "int32_default",
            "tensor_dtype": torch.int32,
            "tensor_mode": "default",
            "range_note": "Retried with int32 tensors to detect dtype-sensitive coverage.",
        },
    ]
    range_profile = get_range_profile(op_name)
    if range_profile is not None:
        profiles.append(range_profile)
    return profiles


def get_example_inputs(
    op_name: str,
    *,
    tensor_dtype: torch.dtype = torch.float32,
    tensor_mode: str = "default",
) -> tuple[Any, ...]:
    """Return simple heuristic inputs for backward compatibility."""
    x = _make_tensor((2, 3), dtype=tensor_dtype, mode=tensor_mode)
    y = _make_tensor((2, 3), dtype=tensor_dtype, mode=tensor_mode)
    if any(token in op_name for token in ("cat", "stack")):
        return (x, y, 1)
    if any(token in op_name for token in ("add", "sub", "mul", "div")):
        return (x, y)
    return (x,)


def build_test_callable(op_name: str):
    """Compile and return the generated heuristic test function for an op."""
    source = generate_test_function(op_name)
    namespace: dict[str, Any] = {"__name__": "compat_tool.generated_tests"}
    exec(source, namespace)
    return namespace[f"test_{_sanitize_identifier(op_name)}"]


def normalize_error(error: BaseException) -> str:
    """Collapse an exception into a concise string for logs and JSON output."""
    message = str(error).strip()
    if not message:
        message = error.__class__.__name__
    return message.replace("\n", " ").strip()


@contextmanager
def time_limit(seconds: int) -> Iterator[None]:
    """Raise TimeoutError if the wrapped block exceeds `seconds` on Unix."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handle_timeout(signum: int, frame: Any) -> None:
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def is_tensor_like_argument(type_name: str) -> bool:
    """Return True if the TableGen argument type looks tensor-shaped."""
    return "tensor" in type_name.lower()


def python_default_for_type(type_name: str) -> Any:
    """Return a stable default example value for a coarse TableGen type."""
    lowered = type_name.lower()
    if "tensor" in lowered:
        return _make_tensor((2, 3), dtype=torch.float32)
    if "bool" in lowered:
        return False
    if "int" in lowered:
        return 1
    if "float" in lowered or "scalar" in lowered or "number" in lowered:
        return 1.0
    if "str" in lowered:
        return "none"
    if "device" in lowered:
        return "cpu"
    if "generator" in lowered:
        return None
    if "list" in lowered or "[]" in lowered:
        return [1]
    if "optional" in lowered:
        return None
    return math.nan


def build_bound_invocation(
    op_name: str,
    op_meta: dict[str, Any],
    *,
    tensor_dtype: torch.dtype = torch.float32,
    tensor_mode: str = "default",
) -> tuple[BoundInvocation, tuple[Any, ...], str]:
    """Build a schema-aware invocation for tracing."""
    tensor_inputs: list[Any] = []
    positional_kinds: list[str] = []
    positional_constants: list[Any | None] = []
    keyword_tensor_constants: dict[str, Any] = {}
    keyword_constants: dict[str, Any] = {}
    tensor_specs: list[str] = []

    operator = resolve_torch_operator(op_name)
    schema = resolve_torch_schema(op_name, operator)

    for index, schema_arg in enumerate(schema.arguments):
        arg_name = schema_arg.name
        arg_type = str(schema_arg.type)
        lowered_type = arg_type.lower()
        kwarg_only = bool(getattr(schema_arg, "kwarg_only", False))

        if "listoftensortype" in lowered_type or "list[tensor]" in lowered_type:
            if _base_name(op_name) == "aten.einsum":
                left = torch.randn((2, 4), dtype=torch.float32)
                right = torch.randn((4, 3), dtype=torch.float32)
            else:
                left = _make_tensor_arg(op_name, f"{arg_name}_0", arg_type, index, tensor_dtype, tensor_mode)
                right = _make_tensor_arg(op_name, f"{arg_name}_1", arg_type, index + 1, tensor_dtype, tensor_mode)
            tensor_specs.append(f"{arg_name}: list[{tuple(left.shape)}, {tuple(right.shape)}]/{str(left.dtype).replace('torch.', '')}")
            if kwarg_only:
                keyword_tensor_constants[arg_name] = [left, right]
            else:
                tensor_inputs.extend([left, right])
                positional_kinds.append("tensor_list")
                positional_constants.append(None)
            continue

        if "tensor" in lowered_type:
            if "optional" in lowered_type and arg_name.lower() == "bias":
                tensor_specs.append(f"{arg_name}: None")
                if kwarg_only:
                    keyword_constants[arg_name] = None
                else:
                    positional_kinds.append("constant")
                    positional_constants.append(None)
                continue
            if "optional" in lowered_type and (
                (_base_name(op_name) == "aten.cross_entropy_loss" and arg_name == "weight")
                or (_base_name(op_name) == "aten.bincount" and arg_name == "weights")
                or (_base_name(op_name) == "aten.embedding_bag" and arg_name == "per_sample_weights")
            ):
                tensor_specs.append(f"{arg_name}: None")
                if kwarg_only:
                    keyword_constants[arg_name] = None
                else:
                    positional_kinds.append("constant")
                    positional_constants.append(None)
                continue

            tensor = _make_tensor_arg(op_name, arg_name, arg_type, index, tensor_dtype, tensor_mode)
            tensor_specs.append(f"{arg_name}: shape={tuple(tensor.shape)} dtype={str(tensor.dtype).replace('torch.', '')}")
            if kwarg_only:
                keyword_tensor_constants[arg_name] = tensor
            else:
                tensor_inputs.append(tensor)
                positional_kinds.append("tensor")
                positional_constants.append(None)
            continue

        constant = _constant_from_type(op_name, arg_name, arg_type, tensor_dtype)
        tensor_specs.append(f"{arg_name}: {constant!r}")
        if kwarg_only:
            keyword_constants[arg_name] = constant
        else:
            positional_kinds.append("constant")
            positional_constants.append(constant)

    invocation = BoundInvocation(
        operator=operator,
        positional_kinds=positional_kinds,
        positional_constants=positional_constants,
        keyword_tensor_constants=keyword_tensor_constants,
        keyword_constants=keyword_constants,
        tensor_specs=tensor_specs,
    )
    return invocation, tuple(tensor_inputs), "; ".join(tensor_specs)


def select_recommended_alternative(op_name: str, database: dict[str, dict[str, Any]]) -> str | None:
    """Pick a supported sibling overload that can be suggested as an alternative."""
    base_name = _base_name(op_name)
    candidates = [
        candidate
        for candidate, info in database.items()
        if candidate != op_name and info.get("supported") and _base_name(candidate) == base_name
    ]
    if not candidates:
        return None

    def _rank(name: str) -> tuple[int, int, str]:
        score = 0
        if ".Tensor" in name:
            score -= 3
        if name == base_name:
            score -= 2
        if name.endswith("_"):
            score += 2
        return (score, len(name), name)

    return sorted(candidates, key=_rank)[0]
