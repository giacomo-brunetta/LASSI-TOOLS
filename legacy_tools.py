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

# Initialize FastMCP server
mcp = FastMCP("LASSI-legacy") 

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

def main():
    # Initialize and run the server
    mcp.run()

if __name__ == "__main__":
    main()
