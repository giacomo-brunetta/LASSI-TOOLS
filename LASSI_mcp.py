from typing import Annotated, Union, List, Optional
from pathlib import Path
from pydantic import Field
import mcp.types as types
import json
import sys
import shutil
import re
import asyncio
import subprocess
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

@mcp.tool()
async def synthesize_tosa_with_soda(
    output_dir: Annotated[
        str,
        Field(description="Path to the output folder containing 01_tosa.mlir")
    ],
    stage: Annotated[
        str,
        Field(description="Makefile STOP_STAGE value, e.g. linalg, llvm-mode-ll, bambu-verilog, or bambu-sim")
    ] = "bambu-verilog",
    build_mode: Annotated[
        str,
        Field(description="SODA build mode: baseline or transformed")
    ] = "transformed",
) -> str:
    """
    Run the shared soda-tools Makefile from an output folder that already contains 01_tosa.mlir.
    The command log is always written to <output_dir>/log.txt.
    """
    resolved_output_dir = Path(output_dir).resolve()
    tosa_path = resolved_output_dir / "01_tosa.mlir"
    log_path = resolved_output_dir / "log.txt"
    makefile_path = Path("/home/gbrun/LASSI-TOOLS/soda-tools/Makefile")

    valid_stages = {
        "tosa",
        "linalg",
        "llvm-mlir",
        "llvm-ll",
        "llvm-mode-mlir",
        "llvm-mode-ll",
        "bambu-verilog",
        "bambu-sim",
    }
    valid_modes = {"baseline", "transformed"}

    if not resolved_output_dir.is_dir():
        return f"Synthesis failed: output directory not found at {resolved_output_dir}"

    if not tosa_path.exists():
        return f"Synthesis failed: expected TOSA MLIR at {tosa_path}"

    if stage not in valid_stages:
        return f"Synthesis failed: unsupported stage '{stage}'. Valid values: {', '.join(sorted(valid_stages))}"

    if build_mode not in valid_modes:
        return f"Synthesis failed: unsupported build_mode '{build_mode}'. Valid values: baseline, transformed"

    if not makefile_path.exists():
        return f"Synthesis failed: soda-tools Makefile not found at {makefile_path}"

    transform_path = resolved_output_dir.parent / "transform.mlir"
    if build_mode == "transformed" and not transform_path.exists():
        alternate_transform_path = resolved_output_dir / "transform.mlir"
        if alternate_transform_path.exists():
            transform_path = alternate_transform_path
        else:
            return (
                "Synthesis failed: transformed mode requires transform.mlir. "
                f"Tried {transform_path} and {alternate_transform_path}"
            )

    cmd = [
        "make",
        "-f",
        str(makefile_path),
        f"ODIR={resolved_output_dir}",
        f"STOP_STAGE={stage}",
        f"BUILD_MODE={build_mode}",
    ]
    if build_mode == "transformed":
        cmd.append(f"TRANSFORM_PATH={transform_path}")

    def _run_make() -> subprocess.CompletedProcess:
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            cmd,
            cwd=str(resolved_output_dir),
            capture_output=True,
            text=True,
        )
        combined_output = []
        combined_output.append(f"$ {' '.join(cmd)}")
        if completed.stdout:
            combined_output.append(completed.stdout)
        if completed.stderr:
            combined_output.append(completed.stderr)
        log_path.write_text("\n".join(combined_output), encoding="utf-8")
        return completed

    try:
        completed = await asyncio.to_thread(_run_make)
    except Exception as e:
        return f"Synthesis failed with internal error: {str(e)}"

    status = "Success" if completed.returncode == 0 else f"Failed (Code {completed.returncode})"
    return (
        f"--- Synthesis {status} ---\n"
        f"output_dir: {resolved_output_dir}\n"
        f"stage: {stage}\n"
        f"build_mode: {build_mode}\n"
        f"log_path: {log_path}"
    )

#============================================================================
#                               RESOURCES
#============================================================================

# TODO all the prompts of the original LASSI prompts can be converted to resources here.

SERVER_ROOT = Path(__file__).resolve().parent
COMPAT_RESOURCE_ROOT = SERVER_ROOT / "resources" / "compatibility"
COMPAT_DB_PATH = COMPAT_RESOURCE_ROOT / "compat_db.json"
COMPAT_WIKI_DIR = COMPAT_RESOURCE_ROOT / "wiki"


def _load_compat_database() -> dict:
    if not COMPAT_DB_PATH.exists():
        return {}
    with COMPAT_DB_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _canonicalize_compat_op_name(raw_name: str, database: dict) -> Optional[str]:
    """
    Normalize common user/agent naming forms to canonical DB keys.
    Examples:
      - torch.matmul -> aten.matmul
      - torch.nn.functional.softmax -> aten.softmax.int / aten.softmax
      - softmax -> aten.softmax.int / aten.softmax
    """
    if not raw_name:
        return None

    name = raw_name.strip()
    if name in database:
        return name

    candidates = []
    lowered = name.lower()

    # Direct aten wrapping for names like "matmul"
    if not lowered.startswith("aten."):
        candidates.append(f"aten.{name}")

    # torch.nn.functional.<op>
    if lowered.startswith("torch.nn.functional."):
        base = name.split(".")[-1]
        candidates.extend([f"aten.{base}.int", f"aten.{base}"])

    # torch.<op>
    if lowered.startswith("torch."):
        suffix = name.split(".", maxsplit=1)[1]
        candidates.extend([f"aten.{suffix}", f"aten.{suffix}.int"])

    # bare op name fallback
    base = name.split(".")[-1]
    candidates.extend([f"aten.{base}.int", f"aten.{base}"])

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate in database:
            return candidate

    return None


@mcp.resource("wiki://help")
def get_wiki_resource_help() -> str:
    """
    Human/agent-facing discovery entry point for all wiki URI patterns.
    """
    database = _load_compat_database()
    return json.dumps(
        {
            "name": "LASSI Compatibility Wiki Resources",
            "canonical_resources": [
                "wiki://help",
                "wiki://compatibility/index",
                "wiki://compatibility/op/{name}",
                "wiki://compatibility/search/{pattern}",
            ],
            "aliases": [
                "wiki://compatibility",
                "wiki://compatibility/function/{name}",
                "wiki://compatibility/torch/{name}",
            ],
            "name_normalization_examples": [
                {"input": "torch.matmul", "canonical": "aten.matmul"},
                {"input": "torch.nn.functional.softmax", "canonical": "aten.softmax.int (if present)"},
                {"input": "softmax", "canonical": "aten.softmax.int or aten.softmax"},
            ],
            "quickstart": [
                "1) Query wiki://compatibility/index",
                "2) Query wiki://compatibility/search/<term>",
                "3) Query wiki://compatibility/op/<op_name>",
            ],
            "database_available": bool(database),
            "total_ops": len(database),
        },
        indent=2,
    )


@mcp.resource("wiki://compatibility")
def get_compatibility_wiki_index_alias() -> str:
    """
    Alias for agents that try the compatibility root directly.
    """
    return get_compatibility_wiki_index()

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


@mcp.resource("wiki://compatibility/index")
def get_compatibility_wiki_index() -> str:
    """
    Returns a compact index of the generated Torch-MLIR/TOSA compatibility wiki.
    """
    if not COMPAT_DB_PATH.exists():
        return f"Compatibility database not found at {COMPAT_DB_PATH}"

    database = _load_compat_database()

    supported = sorted(op_name for op_name, info in database.items() if info.get("supported"))
    unsupported = sorted(op_name for op_name, info in database.items() if not info.get("supported"))

    return json.dumps(
        {
            "database_path": str(COMPAT_DB_PATH),
            "wiki_dir": str(COMPAT_WIKI_DIR),
            "help_uri": "wiki://help",
            "resource_templates": [
                "wiki://compatibility/index",
                "wiki://compatibility/op/{name}",
                "wiki://compatibility/search/{pattern}",
            ],
            "total_ops": len(database),
            "supported_count": len(supported),
            "unsupported_count": len(unsupported),
            "sample_supported": supported[:25],
            "sample_unsupported": unsupported[:25],
        },
        indent=2,
    )


@mcp.resource("wiki://compatibility/op/{name}")
def get_compatibility_wiki_entry(name: str) -> str:
    """
    Returns the generated markdown wiki page for a specific op.
    """
    if not COMPAT_WIKI_DIR.exists():
        return f"Compatibility wiki directory not found at {COMPAT_WIKI_DIR}"

    database = _load_compat_database()

    canonical = _canonicalize_compat_op_name(name, database) or name

    page_path = COMPAT_WIKI_DIR / f"{canonical}.md"
    if page_path.exists():
        return page_path.read_text(encoding="utf-8")

    if database:
        if canonical in database:
            info = database[canonical]
            status = "Supported" if info.get("supported") else "Unsupported"
            error = info.get("error") or "None"
            return (
                f"# {canonical}\n\n"
                f"- Query Input: {name}\n"
                f"- Status: {status}\n"
                f"- Error: {error}\n"
            )

    suggestions = []
    lowered = name.lower().strip()
    for op_name in sorted(database.keys()):
        if lowered and lowered in op_name.lower():
            suggestions.append(op_name)
        if len(suggestions) >= 10:
            break

    return json.dumps(
        {
            "error": f"No compatibility wiki entry found for op: {name}",
            "help_uri": "wiki://help",
            "try_search_uri": f"wiki://compatibility/search/{name}",
            "valid_template": "wiki://compatibility/op/{name}",
            "normalized_candidate": _canonicalize_compat_op_name(name, database),
            "suggestions": suggestions,
        },
        indent=2,
    )


@mcp.resource("wiki://compatibility/function/{name}")
def get_compatibility_wiki_entry_function_alias(name: str) -> str:
    """
    Alias for agents that use 'function' wording instead of op name.
    """
    return get_compatibility_wiki_entry(name)


@mcp.resource("wiki://compatibility/torch/{name}")
def get_compatibility_wiki_entry_torch_alias(name: str) -> str:
    """
    Alias for agents that query torch-style names directly.
    """
    return get_compatibility_wiki_entry(f"torch.{name}")


@mcp.resource("wiki://compatibility/search/{pattern}")
def search_compatibility_wiki(pattern: str) -> str:
    """
    Search compatibility entries by substring.

    Prefix the pattern with `supported:` or `unsupported:` to filter results.
    Examples:
      - wiki://compatibility/search/relu
      - wiki://compatibility/search/supported:relu
      - wiki://compatibility/search/unsupported:softmax
    """
    if not COMPAT_DB_PATH.exists():
        return f"Compatibility database not found at {COMPAT_DB_PATH}"

    database = _load_compat_database()

    support_filter = None
    needle = pattern.strip()
    lowered = needle.lower()

    if lowered.startswith("supported:"):
        support_filter = True
        needle = needle.split(":", maxsplit=1)[1].strip()
    elif lowered.startswith("unsupported:"):
        support_filter = False
        needle = needle.split(":", maxsplit=1)[1].strip()

    matches = []
    normalized_candidate = _canonicalize_compat_op_name(needle, database)
    needle_lower = needle.lower()
    for op_name, info in sorted(database.items()):
        if needle_lower and needle_lower not in op_name.lower():
            continue
        if support_filter is not None and bool(info.get("supported")) is not support_filter:
            continue
        matches.append(
            {
                "op_name": op_name,
                "supported": bool(info.get("supported")),
                "error": info.get("error"),
                "uri": f"wiki://compatibility/op/{op_name}",
            }
        )

    # If no substring matches, try a normalized direct match (torch.* -> aten.* etc.)
    if not matches and normalized_candidate and normalized_candidate in database:
        info = database[normalized_candidate]
        matches.append(
            {
                "op_name": normalized_candidate,
                "supported": bool(info.get("supported")),
                "error": info.get("error"),
                "uri": f"wiki://compatibility/op/{normalized_candidate}",
                "normalized_from": pattern,
            }
        )

    return json.dumps(
        {
            "pattern": pattern,
            "normalized_candidate": normalized_candidate,
            "help_uri": "wiki://help",
            "match_count": len(matches),
            "matches": matches[:100],
        },
        indent=2,
    )

def main():
    # Initialize and run the server
    mcp.run()

if __name__ == "__main__":
    main()
