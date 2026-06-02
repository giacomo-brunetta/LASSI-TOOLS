from __future__ import annotations

from pathlib import Path
from typing import List

import torch


def _build_inputs(inputs_spec: List[dict]):
    tensors = []
    for inp in inputs_spec:
        shape = inp.get("shape")
        dtype = inp.get("dtype", "float32")

        if dtype == "float32":
            tensor = torch.randn(*shape)
        elif dtype == "int64":
            tensor = torch.randint(0, 10, shape)
        else:
            raise ValueError(f"Unsupported dtype: {dtype}")

        tensors.append(tensor)

    return tuple(tensors)


def _compile_with_frontend(model, inputs, target: str, frontend: str):
    import torch_mlir

    target_map = {
        "torch": "torch",
        "linalg": "linalg-on-tensors",
        "linalg-on-tensors": "linalg-on-tensors",
        "tosa": "tosa",
        "stablehlo": "stablehlo",
    }
    normalized_target = target_map.get(target, target)

    if frontend == "torchscript":
        if hasattr(torch_mlir, "compile"):
            return torch_mlir.compile(model, inputs, output_type=normalized_target)
        try:
            from torch_mlir import torchscript as torchscript_frontend

            return torchscript_frontend.compile(
                model,
                inputs,
                output_type=normalized_target,
            )
        except ImportError:
            pass
        raise RuntimeError("No TorchScript compile API found in torch-mlir")

    if frontend == "fx":
        try:
            from torch_mlir import fx as fx_frontend

            return fx_frontend.export_and_import(
                model,
                inputs,
                output_type=normalized_target,
            )
        except ImportError:
            pass
        raise RuntimeError("FX frontend not available in this torch-mlir version")

    if frontend == "export":
        exported = torch.export.export(model, inputs)
        if hasattr(torch_mlir, "compile"):
            return torch_mlir.compile(exported, output_type=normalized_target)
        raise RuntimeError("Export frontend not supported in this version")

    raise ValueError(f"Unknown frontend: {frontend}")


def _load_model(model_path: Path):
    try:
        return torch.jit.load(str(model_path), map_location="cpu")
    except Exception:
        return torch.load(str(model_path), map_location="cpu")


async def compile_torch_to_mlir_impl(
    model_path: str,
    inputs: List[dict],
    target: str = "linalg-on-tensors",
    frontend: str = "torchscript",
    validate: bool = True,
    output_path: str | None = None,
) -> str:
    """
    Compile a PyTorch .pt model into MLIR using torch-mlir.
    """
    try:
        resolved_model_path = Path(model_path).resolve()
        if not resolved_model_path.exists():
            return f"[Compilation Error]\nModel file not found: {resolved_model_path}"

        if output_path:
            resolved_output_path = Path(output_path).resolve()
        else:
            resolved_output_path = resolved_model_path.with_suffix(".mlir")

        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

        model = _load_model(resolved_model_path)
        model.eval()

        example_inputs = _build_inputs(inputs)

        if validate:
            try:
                with torch.no_grad():
                    model(*example_inputs)
            except Exception as exc:
                return f"[Validation Error]\n{str(exc)}"

        mlir_module = _compile_with_frontend(
            model,
            example_inputs,
            target,
            frontend,
        )

        resolved_output_path.write_text(str(mlir_module), encoding="utf-8")
        return f"MLIR written to {resolved_output_path}"
    except Exception as exc:
        return f"[Compilation Error]\n{str(exc)}"
