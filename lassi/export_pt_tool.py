from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import importlib.util

import torch


def _load_module_from_file(path: Path):
    spec = importlib.util.spec_from_file_location("user_model", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {path}")

    module = importlib.util.module_from_spec(spec)
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
            try:
                scripted = torch.jit.script(model)
            except Exception:
                if input_shape is None:
                    return "[Error] input_shape required for tracing fallback"

                example_input = torch.randn(*input_shape)
                scripted = torch.jit.trace(model, example_input)

            torch.jit.save(scripted, str(target_path))
        else:
            return f"[Error] Unknown export_type: {export_type}"

        return f"Model successfully exported to {target_path}"
    except Exception as exc:
        return f"[Export Error]\n{str(exc)}"
