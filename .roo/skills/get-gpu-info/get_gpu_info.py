import asyncio
import shutil
import sys

async def get_gpu_info():
    async def run_cmd(cmd_args):
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return f"Error: {stderr.decode().strip()}"
            return stdout.decode().strip()
        except Exception as e:
            return f"Execution failed: {str(e)}"

    if shutil.which("nvidia-smi"):
        output = await run_cmd([
            "nvidia-smi", 
            "--query-gpu=name,memory.total,memory.free,utilization.gpu", 
            "--format=csv"
        ])
        print(f"NVIDIA GPU Detected:\n{output}")

    elif shutil.which("rocm-smi"):
        output = await run_cmd([
            "rocm-smi", "--showproductname", "--showmeminfo", "vram"
        ])
        print(f"AMD GPU Detected:\n{output}")

    elif shutil.which("xpu-smi"):
        output = await run_cmd(["xpu-smi", "dump"])
        print(f"Intel GPU Detected:\n{output}")

    else:
        print("No dedicated GPU management tools (nvidia-smi, rocm-smi, xpu-smi) were found.")

if __name__ == "__main__":
    asyncio.run(get_gpu_info())
