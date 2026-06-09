from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys


def _run_version_cmd(cmd: list[str]) -> dict:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return {
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as exc:
        return {
            "command": cmd,
            "error": str(exc),
        }


async def get_toolchain_info_impl() -> str:
    """Return the effective Python/torch/torch-mlir/LLVM-related toolchain
    information from the current runtime environment as JSON."""
    info: dict = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "version_info": list(sys.version_info[:3]),
            "platform": platform.platform(),
        },
        "environment": {
            "cwd": os.getcwd(),
            "pythonpath": os.environ.get("PYTHONPATH", ""),
            "path": os.environ.get("PATH", ""),
        },
    }

    try:
        import torch

        info["torch"] = {
            "importable": True,
            "version": getattr(torch, "__version__", None),
            "module_file": getattr(torch, "__file__", None),
        }
    except Exception as exc:
        info["torch"] = {
            "importable": False,
            "error": str(exc),
        }

    try:
        import torch_mlir

        info["torch_mlir"] = {
            "importable": True,
            "module_file": getattr(torch_mlir, "__file__", None),
            "module_path": [str(p) for p in getattr(torch_mlir, "__path__", [])],
            "version": getattr(torch_mlir, "__version__", None),
        }
    except Exception as exc:
        info["torch_mlir"] = {
            "importable": False,
            "error": str(exc),
        }

    try:
        import torch_mlir.torchscript as torch_mlir_torchscript

        info.setdefault("torch_mlir", {})
        info["torch_mlir"]["torchscript_importable"] = True
        info["torch_mlir"]["torchscript_module_file"] = getattr(
            torch_mlir_torchscript,
            "__file__",
            None,
        )
        info["torch_mlir"]["torchscript_compile_available"] = hasattr(
            torch_mlir_torchscript,
            "compile",
        )
    except Exception as exc:
        info.setdefault("torch_mlir", {})
        info["torch_mlir"]["torchscript_importable"] = False
        info["torch_mlir"]["torchscript_error"] = str(exc)

    for tool_name in ["clang", "clang++", "llvm-config", "mlir-opt", "torch-mlir-opt"]:
        tool_path = shutil.which(tool_name)
        tool_info = {
            "path": tool_path,
            "available": tool_path is not None,
        }
        if tool_path:
            tool_info["version_probe"] = _run_version_cmd([tool_name, "--version"])
        info[tool_name] = tool_info

    return json.dumps(info, indent=2)
