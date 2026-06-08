from __future__ import annotations

import asyncio
import json
import shutil


async def get_machine_info_impl() -> str:
    def _get_info():
        import psutil

        cpu_freq = psutil.cpu_freq()
        cpu_info = {
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "frequency_mhz": cpu_freq._asdict() if cpu_freq else "N/A",
            "usage_percent": psutil.cpu_percent(interval=0.1),
        }

        vm = psutil.virtual_memory()
        ram_info = {
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "usage_percent": vm.percent,
        }

        return {"cpu": cpu_info, "ram": ram_info}

    try:
        info = await asyncio.to_thread(_get_info)
        return json.dumps(info, indent=2)
    except Exception as exc:
        return f"Error retrieving machine info: {str(exc)}"


async def get_gpu_info_impl() -> str:
    async def run_cmd(cmd_args: list[str]) -> str:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                return f"Error: {stderr.decode().strip()}"
            return stdout.decode().strip()
        except Exception as exc:
            return f"Execution failed: {str(exc)}"

    if shutil.which("nvidia-smi"):
        output = await run_cmd(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free,utilization.gpu",
                "--format=csv",
            ]
        )
        return f"NVIDIA GPU Detected:\n{output}"

    if shutil.which("rocm-smi"):
        output = await run_cmd(["rocm-smi", "--showproductname", "--showmeminfo", "vram"])
        return f"AMD GPU Detected:\n{output}"

    if shutil.which("xpu-smi"):
        output = await run_cmd(["xpu-smi", "dump"])
        return f"Intel GPU Detected:\n{output}"

    return "No dedicated GPU management tools (nvidia-smi, rocm-smi, xpu-smi) were found."
