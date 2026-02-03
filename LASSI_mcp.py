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

# Initialize FastMCP server
mcp = FastMCP("LASSI") 

#============================================================================
#                                   TOOLS
#============================================================================

@mcp.tool()
async def compile_source(
    path: Annotated[Union[str, List[str]], Field(description="The absolute path or list of paths to the source file(s) to compile.")],
    compiler: Annotated[str, Field(description="The compiler to use (e.g. 'gcc', 'nvcc').")],
    kwds: Annotated[str, Field(description="Compiler flags (e.g. '-O3 -Wall').")] = None,
    includes: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the include directory(ies).")] = None,
    libraries: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the library directory(ies).")] = None,
    output: Annotated[str, Field(description="The output binary file name.")] = None,
) -> str:
    """
    Compiles one or more source files using a specific compiler.
    """
    if isinstance(path, str):
        target_paths = [Path(path).resolve()]
    else:
        target_paths = [Path(p).resolve() for p in path]

    output_path = Path(output).resolve() if output else None

    for p in target_paths:
        if not p.exists():
            return f"Compilation failed: File not found at {p}"

    # 3. Logic: Resolve the Compiler Enum
    try:
        compiler_tool = CompilerTool.from_string(compiler.lower())
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    # 4. Execution
    try:
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=kwds,
            include_dirs=includes,
            library_dirs=libraries,
            output_file=output_path
        )
        return f"Compilation successful. Binary created at: {result_path.name}"
    except Exception as e:
        return f"Compilation failed: {str(e)}"
    
@mcp.tool()
async def compile_to_mlir(
    path: Annotated[Union[str, List[str]], Field(description="The absolute path or list of paths to the source file(s) to compile.")],
    kwds: Annotated[str, Field(description="Specific flags for cgeist (e.g., '-function=*').")] = None,
    includes: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the include directory(ies).")] = None,
    libraries: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the library directory(ies).")] = None,
    output: Annotated[str, Field(description="The output MLIR file name.")] = None,
) -> str:
    """
    Compiles C/C++ source file(s) specifically to MLIR using cgeist.
    """
    if isinstance(path, str):
        target_paths = [Path(path).resolve()]
    else:
        target_paths = [Path(p).resolve() for p in path]

    output_path = Path(output).resolve() if output else None

    for p in target_paths:
        if not p.exists():
            return f"Compilation failed: File not found at {p}"

    try:
        # 3. Execution
        compiler_tool = CompilerTool(Compiler.CGEIST)
        
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=kwds,
            include_dirs=includes,
            library_dirs=libraries,
            output_file=output_path
        )
        return f"MLIR generation successful. Output file: {result_path.name}"
    
    except Exception as e:
        return f"MLIR generation failed: {str(e)}"

@mcp.tool()
async def compile_with_libtorch(
    path: Annotated[Union[str, List[str]], Field(description="The absolute path or list of paths to the source file(s) to compile.")],
    kwds: Annotated[str, Field(description="Flags for GPP")] = None,
    includes: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the include directory(ies).")] = None,
    libraries: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the library directory(ies).")] = None,
    output: Annotated[str, Field(description="The output file name.")] = None,
) -> str:
    """
    Compiles C++ file(s). Automatically finds libtorch include and lib paths and adds them to the compilation command.
    """
    print(f"DEBUG: Received path={path}", file=sys.stderr)
    if isinstance(path, str):
        target_paths = [Path(path).resolve()]
    else:
        target_paths = [Path(p).resolve() for p in path]
    print(f"DEBUG: Resolved target_paths={target_paths}", file=sys.stderr)

    output_path = Path(output).resolve() if output else None

    for p in target_paths:
        if not p.exists():
            return f"Compilation failed: File not found at {p}"

    torch_paths = CompilerTool.find_torchlib_paths()
    torch_inc = torch_paths["TORCH_INC"]
    torch_api_inc = torch_paths["TORCH_API_INC"]
    torch_lib = torch_paths["TORCH_LIB"]

    # Handle includes and libraries lists
    if includes is None:
        includes = []
    elif isinstance(includes, str):
        includes = [includes]
    else:
        includes = list(includes)
    includes.extend([str(torch_inc), str(torch_api_inc)])

    if libraries is None:
        libraries = []
    elif isinstance(libraries, str):
        libraries = [libraries]
    else:
        libraries = list(libraries)
    libraries.append(str(torch_lib))

    abi_flag = "-D_GLIBCXX_USE_CXX11_ABI=1"
    std_flag = "-std=c++17"

    flag_parts = []
    if kwds:
        flag_parts.append(kwds.strip())
    flag_parts.extend(["-O3", std_flag, abi_flag])
    
    # Specific libtorch linkage flags
    lib_link_flags = [
        "-ltorch",
        "-ltorch_cpu",
        "-ltorch_cuda",
        "-lc10",
        "-lpthread",
        "-ldl",
        "-lrt",
        f"-Wl,-rpath,{torch_lib}",
    ]
    flag_parts.extend(lib_link_flags)

    kwds = " ".join(flag_parts)

    # 2. Validation
    try:
        # 3. Execution
        compiler_tool = CompilerTool(Compiler.GPP)
        
        print(f"DEBUG: Calling compile with files={target_paths}, kwds={kwds}, includes={includes}, libraries={libraries}", file=sys.stderr)
        result_path = compiler_tool.compile(
            files=target_paths,
            kwds=kwds,
            include_dirs=includes,
            library_dirs=libraries,
            output_file=output_path
        )
        return f"Compilation successful. Binary created at: {result_path.name}"
    
    except Exception as e:
        return f"Compilation failed: {str(e)}"

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

async def _push_callgraph_to_memory_impl(
    path: Union[str, List[str]],
    compiler: str = None,
    kwds: str = None,
    includes: Union[str, List[str]] = None,
    libraries: Union[str, List[str]] = None,
    args: str = ""
) -> str:
    """Internal implementation of pushing callgraph to memory."""
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

    # 1. Run profiling to generate gmon.out and get raw gprof output
    compile_flags = (kwds + " " if kwds else "") + "-pg -no-pie -fno-builtin"
    gprof_exe = gprofile.source_file.full_path.parent / (gprofile.source_file.file_name.stem + "_gprof.out")

    gprofile.source_file.compile(
        kwds=compile_flags,
        include_dirs=includes,
        library_dirs=libraries,
        extra_files=extra_files,
        output_file=gprof_exe
    )
    
    if not gprofile.source_file.is_compiled():
        return "Compilation failed."

    # Execute the binary to generate gmon.out
    gprofile.source_file.execute(args=args)

    if not gprofile.source_file.executable:
        return "Executable not found."

    exe_path = gprofile.source_file.executable.resolve()
    cmd = ["gprof", str(exe_path), "gmon.out", "-q"]

    import subprocess
    gprof_result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if gprof_result.returncode != 0:
        return f"gprof failed: {gprof_result.stderr.strip()}"

    # 2. Parse gprof output
    from lassi.gprof import parse_gprof_to_memory_schema
    entities, relations = parse_gprof_to_memory_schema(gprof_result.stdout)

    # Deduplicate relations
    unique_rels = []
    seen = set()
    for r in relations:
        key = (r['from'], r['to'], r['relationType'])
        if key not in seen:
            seen.add(key)
            unique_rels.append(r)

    # 3. Connect to Memory MCP Server and push
    docker_path = shutil.which("docker")
    if not docker_path:
        return "Docker not found in path. Cannot connect to memory server."

    server_params = StdioServerParameters(
        command=docker_path,
        args=["run", "-i", "--rm", "-v", "mcp-memory-data:/app/dist", "mcp/memory"]
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                nodes_pushed = 0
                edges_pushed = 0

                if entities:
                    await session.call_tool("create_entities", arguments={"entities": entities})
                    nodes_pushed = len(entities)
                
                if unique_rels:
                    await session.call_tool("create_relations", arguments={"relations": unique_rels})
                    edges_pushed = len(unique_rels)

                return f"Successfully pushed callgraph to memory: {nodes_pushed} nodes, {edges_pushed} edges."
    except Exception as e:
        return f"Failed to push to memory server: {str(e)}"

@mcp.tool()
async def push_callgraph_to_memory(
    path: Annotated[Union[str, List[str]], Field(description="The absolute path or list of paths to the source file(s) to compile.")],
    compiler: Annotated[str, Field(description="The compiler to use (e.g. 'gcc', 'nvcc').")] = None,
    kwds: Annotated[str, Field(description="Compiler flags (e.g. '-O3 -Wall'). Gprof-specific flags (e.g. -pg) are added by default.")] = None,
    includes: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the include directory(ies).")] = None,
    libraries: Annotated[Union[str, List[str]], Field(description="The absolute path(s) to the library directory(ies).")] = None,
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = ""
) -> str:
    """
    Runs gprof to get the callgraph and pushes it to the Memory MCP server.
    """
    return await _push_callgraph_to_memory_impl(path, compiler, kwds, includes, libraries, args)

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
