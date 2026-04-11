from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import importlib.util
import sys

import torch


def _build_trace_input(input_shape: list):
    # Single input: [d0, d1, ...]
    # Multi-input: [[...], [...], ...]
    if len(input_shape) > 0 and isinstance(input_shape[0], (list, tuple)):
        return tuple(torch.randn(*shape) for shape in input_shape)
    return torch.randn(*input_shape)


def _load_module_from_file(path: Path):
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")

    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _instantiate_model(module, class_name: str, init_args: Optional[Dict[str, Any]]):
    model_class = getattr(module, class_name)
    return model_class(**(init_args or {}))


async def export_model_to_pt_impl(
    model_file: str,
    class_name: str,
    output_path: str,
    init_args: Optional[Dict[str, Any]] = None,
    weights_path: Optional[str] = None,
    export_type: str = "torchscript",
    input_shape: Optional[list] = None,
) -> str:
    """
    Load a PyTorch model from a Python file and export it to a .pt file.
    """
    try:
        model_path = Path(model_file).resolve()
        target_path = Path(output_path).resolve()

        if not model_path.exists():
            return f"[Export Error]\nModel file not found: {model_path}"

        if weights_path:
            resolved_weights_path = Path(weights_path).resolve()
            if not resolved_weights_path.exists():
                return f"[Export Error]\nWeights file not found: {resolved_weights_path}"
        else:
            resolved_weights_path = None

        target_path.parent.mkdir(parents=True, exist_ok=True)

        module = _load_module_from_file(model_path)
        model = _instantiate_model(module, class_name, init_args)
        model.eval()

        if resolved_weights_path:
            state_dict = torch.load(str(resolved_weights_path), map_location="cpu")
            model.load_state_dict(state_dict)

        if export_type == "state_dict":
            torch.save(model.state_dict(), str(target_path))
        elif export_type == "full":
            torch.save(model, str(target_path))
        elif export_type == "torchscript":
            # If input_shape is provided, prefer tracing to preserve concrete
            # argument structure/ranks for downstream lowering.
            if input_shape is not None:
                example_input = _build_trace_input(input_shape)
                scripted = torch.jit.trace(model, example_input)
            else:
                try:
                    scripted = torch.jit.script(model)
                except Exception:
                    return "[Error] input_shape required for tracing fallback"

            torch.jit.save(scripted, str(target_path))
        else:
            return f"[Error] Unknown export_type: {export_type}"

        return f"Model successfully exported to {target_path}"
    except Exception as exc:
        return f"[Export Error]\n{str(exc)}"
