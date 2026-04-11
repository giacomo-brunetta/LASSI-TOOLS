from typing import Annotated, Union, List
from pathlib import Path
from pydantic import Field
import mcp.types as types
import json
import sys
import shutil
import re
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from fastmcp import FastMCP

from lassi.profiler import Timer
from lassi.compiler import Compiler, CompilerTool, CompilationError, COMPILER_FLAGS_DB
from lassi.source_file import SourceFile
from lassi.executer import FunctionalValidator, ExecTool
from lassi.profiler import MultiProfiler, CPUProfiler, GPUProfiler, ArmPowerProbe, NvidiaPowerProbe
from lassi.gprof import GProf
from lassi.export_pt_tool import export_model_to_pt_impl
from lassi.torch_to_mlir_tool import compile_torch_to_mlir_impl
from lassi.toolchain_info import get_toolchain_info_impl
from lassi.csv_tools import (
    summarize_csv_impl,
    compare_csv_outputs_impl,
    diff_csv_outputs_impl,
)

# Initialize FastMCP server
mcp = FastMCP("LASSI") 

#============================================================================
#                                   TOOLS
#============================================================================

@mcp.tool()
async def gprof_profiling(
    path: Annotated[Union[str, List[str]], Field(description="The absolute path or list of paths to the source file(s) to compile.")],
    compiler: Annotated[str, Field(description="The compiler to use (e.g. 'gcc', 'nvcc').")] = None,
    kwds: Annotated[str, Field(description="Compiler flags (e.g. '-O3 -Wall'). Gprof-specific flags (e.g. -pg) are added by default.")] = None,
    includes: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the include directory(ies).")] = None,
    libraries: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the library directory(ies).")] = None,
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = ""
) -> str:
    """
    Compile file(s) using gprof and returns the callgraph information.
    """

    if isinstance(path, str):
        target_path = Path(path).resolve()
        extra_files = None
    else:
        target_path = Path(path[0]).resolve()
        extra_files = [Path(p).resolve() for p in path[1:]]
    
    gprofile = GProf(
        target_path,
        compiler_tool=CompilerTool.from_string(compiler.lower()) if compiler else None
        )

    return gprofile.profile(
            args=args,
            kwds=kwds if kwds else "",
            include_dirs=includes,
            library_dirs=libraries,
            extra_files=extra_files,
        )

@mcp.tool()
async def execute_with_latency(
    path: Annotated[str, Field(description="The absolute path to the executable binary.")],
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = "",
    dump_output: Annotated[str, Field(description="Optional path to dump the stdout to a file.")] = None,
    expected_output: Annotated[str, Field(description="Optional path or string to compare the output against.")] = None
) -> str:
    """
    Runs an executable and returns both the output and the execution time.
    """
    target_path = Path(path).resolve()

    if not target_path.exists():
        return f"Execution failed: Executable not found at {target_path}"

    # Initialize the tool with the Timer profiler
    # Note: We assume 'Timer' is imported or available in your scope
    executer = ExecTool(executable=target_path, profiler=Timer())

    validator = FunctionalValidator(golden_output=expected_output) if expected_output else None

    try:
        # 1. Run the execution
        # Use asyncio.to_thread to run the blocking executer.run without stalling the event loop
        process_result = await asyncio.to_thread(executer.run, args=args, dump_output=dump_output, validator=validator)

        # 2. Retrieve the profiling report (time, memory, etc.)
        # Since we didn't pass a custom profiler to .run(), it used self.profiler 
        # and saved the result to history.
        report = executer.get_last_execution_report()

        # 3. Construct the response for the LLM
        # We need to combine the Program Output + The Profiling Stats
        output_parts = []
        
        # Header
        status = "Success" if process_result.returncode == 0 else f"Failed (Code {process_result.returncode})"
        output_parts.append(f"--- Execution {status} ---")
        
        # The Report (Timing)
        output_parts.append(f"Profile Report: {report}") 

        # Standard Output (truncated if too long, optional safety measure)
        if process_result.stdout:
            output_parts.append("\n--- Stdout ---")
            output_parts.append(process_result.stdout.strip())
            
        # Standard Error (important for debugging)
        if process_result.stderr:
            output_parts.append("\n--- Stderr ---")
            output_parts.append(process_result.stderr.strip())

        return "\n".join(output_parts)

    except Exception as e:
        return f"Execution failed with internal error: {str(e)}"

@mcp.tool()
async def execute_with_profile(
    path: Annotated[str, Field(description="The absolute path to the executable binary.")],
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = "",
    dump_output: Annotated[str, Field(description="Optional path to dump the stdout to a file.")] = None,
    expected_output: Annotated[str, Field(description="Optional path or string to compare the output against.")] = None
) -> str:
    """
    Runs an executable and returns both the output and the execution power profiling report.
    """
    target_path = Path(path).resolve()

    if not target_path.exists():
        return f"Execution failed: Executable not found at {target_path}"

    executer = ExecTool(
        executable=target_path,
        profiler=MultiProfiler([
                    Timer(),
                    CPUProfiler(ArmPowerProbe()),
                    GPUProfiler(NvidiaPowerProbe())]
            )
        )

    validator = FunctionalValidator(golden_output=expected_output) if expected_output else None

    try:
        # 1. Run the execution
        # Use asyncio.to_thread to run the blocking executer.run without stalling the event loop
        process_result = await asyncio.to_thread(executer.run, args=args, dump_output=dump_output, validator=validator)

        # 2. Retrieve the profiling report (time, memory, etc.)
        # Since we didn't pass a custom profiler to .run(), it used self.profiler 
        # and saved the result to history.
        report = executer.get_last_execution_report()

        # 3. Construct the response for the LLM
        # We need to combine the Program Output + The Profiling Stats
        output_parts = []
        
        # Header
        status = "Success" if process_result.returncode == 0 else f"Failed (Code {process_result.returncode})"
        output_parts.append(f"--- Execution {status} ---")
        
        # The Report (Timing)
        output_parts.append(f"Profile Report: {report}") 

        # Standard Output (truncated if too long, optional safety measure)
        if process_result.stdout:
            output_parts.append("\n--- Stdout ---")
            output_parts.append(process_result.stdout.strip())
            
        # Standard Error (important for debugging)
        if process_result.stderr:
            output_parts.append("\n--- Stderr ---")
            output_parts.append(process_result.stderr.strip())

        return "\n".join(output_parts)

    except Exception as e:
        return f"Execution failed with internal error: {str(e)}"

@mcp.tool()
async def get_machine_info() -> str:
    """
    Reads the CPU and RAM information of this machine.
    """
    def _get_info():
        import psutil
        cpu_freq = psutil.cpu_freq()
        cpu_info = {
            "count_logical": psutil.cpu_count(logical=True),
            "count_physical": psutil.cpu_count(logical=False),
            "frequency_mhz": cpu_freq._asdict() if cpu_freq else "N/A",
            "usage_percent": psutil.cpu_percent(interval=0.1)
        }
        
        vm = psutil.virtual_memory()
        ram_info = {
            "total_gb": round(vm.total / (1024**3), 2),
            "available_gb": round(vm.available / (1024**3), 2),
            "used_gb": round(vm.used / (1024**3), 2),
            "usage_percent": vm.percent
        }
        
        return {
            "cpu": cpu_info,
            "ram": ram_info
        }

    try:
        info = await asyncio.to_thread(_get_info)
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error retrieving machine info: {str(e)}"

@mcp.tool()
async def get_gpu_info() -> str:
    """
    Asynchronously retrieves GPU information using available SMI tools.
    """
    
    # Helper to run async subprocess
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

    # 1. NVIDIA
    if shutil.which("nvidia-smi"):
        output = await run_cmd([
            "nvidia-smi", 
            "--query-gpu=name,memory.total,memory.free,utilization.gpu", 
            "--format=csv"
        ])
        return f"NVIDIA GPU Detected:\n{output}"

    # 2. AMD (ROCm)
    elif shutil.which("rocm-smi"):
        output = await run_cmd([
            "rocm-smi", "--showproductname", "--showmeminfo", "vram"
        ])
        return f"AMD GPU Detected:\n{output}"

    # 3. Intel (XPU)
    elif shutil.which("xpu-smi"):
        output = await run_cmd(["xpu-smi", "dump"])
        return f"Intel GPU Detected:\n{output}"

    return "No dedicated GPU management tools (nvidia-smi, rocm-smi, xpu-smi) were found."

@mcp.tool()
async def get_toolchain_info() -> str:
    """
    Return the effective Python, torch, torch-mlir, and LLVM-related toolchain
    information from the MCP server runtime environment.
    """
    return await get_toolchain_info_impl()

@mcp.tool()
async def summarize_csv(
    path: Annotated[str, Field(description="Path to the CSV file to summarize.")]
) -> str:
    """
    Summarize a numeric CSV file: shape, size, range, mean/std, and NaN/Inf presence.
    """
    return await summarize_csv_impl(path)

@mcp.tool()
async def compare_csv_outputs(
    golden_csv: Annotated[str, Field(description="Path to the golden/oracle CSV file.")],
    candidate_csv: Annotated[str, Field(description="Path to the candidate CSV file.")],
    rtol: Annotated[float, Field(description="Relative tolerance for numeric comparison.")] = 1e-6,
    atol: Annotated[float, Field(description="Absolute tolerance for numeric comparison.")] = 1e-6,
    expected_shape: Annotated[Union[List[int], None], Field(description="Optional expected CSV array shape.")] = None,
) -> str:
    """
    Compare two numeric CSV outputs and return exact/tolerant match status plus error metrics.
    """
    return await compare_csv_outputs_impl(
        golden_csv=golden_csv,
        candidate_csv=candidate_csv,
        rtol=rtol,
        atol=atol,
        expected_shape=expected_shape,
    )

@mcp.tool()
async def diff_csv_outputs(
    golden_csv: Annotated[str, Field(description="Path to the golden/oracle CSV file.")],
    candidate_csv: Annotated[str, Field(description="Path to the candidate CSV file.")],
    output_path: Annotated[Union[str, None], Field(description="Optional path to save the mismatch report as JSON.")] = None,
    max_rows: Annotated[int, Field(description="Maximum number of mismatches to report.")] = 20,
) -> str:
    """
    Report element-wise CSV mismatches, optionally writing the mismatch report to disk.
    """
    return await diff_csv_outputs_impl(
        golden_csv=golden_csv,
        candidate_csv=candidate_csv,
        output_path=output_path,
        max_rows=max_rows,
    )

@mcp.tool()
async def export_model_to_pt(
    model_file: Annotated[
        str,
        Field(description="Path to Python file containing the model class")
    ],
    class_name: Annotated[
        str,
        Field(description="Name of the model class to instantiate")
    ],
    output_path: Annotated[
        str,
        Field(description="Path to save the exported .pt file")
    ],
    init_args: Annotated[
        Union[dict, None],
        Field(description="Constructor arguments for the model")
    ] = None,
    weights_path: Annotated[
        Union[str, None],
        Field(description="Optional path to state_dict weights (.pth)")
    ] = None,
    export_type: Annotated[
        str,
        Field(description="Export format: torchscript, state_dict, or full")
    ] = "torchscript",
    input_shape: Annotated[
        Union[list, None],
        Field(description="Required for tracing if scripting fails")
    ] = None,
) -> str:
    """
    Load a PyTorch model from a Python file and export it to a .pt file.
    """
    return await export_model_to_pt_impl(
        model_file=model_file,
        class_name=class_name,
        output_path=output_path,
        init_args=init_args,
        weights_path=weights_path,
        export_type=export_type,
        input_shape=input_shape,
    )

@mcp.tool()
async def compile_torch_to_mlir(
    model_path: Annotated[str, Field(description="Path to the .pt model file")],
    inputs: Annotated[
        List[dict],
        Field(description="List of input specs, e.g. [{'shape':[1,3,224,224],'dtype':'float32'}]")
    ],
    target: Annotated[
        str,
        Field(description="Desired MLIR dialect: torch, linalg, linalg-on-tensors, tosa, or stablehlo")
    ] = "linalg-on-tensors",
    frontend: Annotated[
        str,
        Field(description="Frontend to use for tracing: torchscript, fx, or export")
    ] = "torchscript",
    validate: Annotated[
        bool,
        Field(description="Run a dry forward pass before compiling")
    ] = True,
    output_path: Annotated[
        Union[str, None],
        Field(description="Optional path to save the generated MLIR. Defaults to the model path with a .mlir extension.")
    ] = None,
) -> str:
    """
    Compile a PyTorch .pt model into MLIR using torch-mlir.
    """
    return await compile_torch_to_mlir_impl(
        model_path=model_path,
        inputs=inputs,
        target=target,
        frontend=frontend,
        validate=validate,
        output_path=output_path,
    )

#============================================================================
#                               RESOURCES
#============================================================================

# TODO all the prompts of the original LASSI prompts can be converted to resources here.

@mcp.resource("compiler://{name}/flags")
def get_compiler_flags(name: str) -> str:
    """
    Returns a cheat-sheet of common flags for the specified compiler.
    """
    # Normalize input using your Enum logic if needed, or simple string matching
    compiler_key = name.lower().strip()
    
    # Fetch data
    flags_data = COMPILER_FLAGS_DB.get(compiler_key)
    
    if not flags_data:
        # Provide a helpful error inside the resource so the LLM knows why it's empty
        return f"No flag documentation found for compiler: {name}. Supported: {list(COMPILER_FLAGS_DB.keys())}"

    # Return as formatted JSON string
    return json.dumps(flags_data, indent=2)

def main():
    # Initialize and run the server
    mcp.run()

if __name__ == "__main__":
    main()
