from typing import Annotated
from pathlib import Path
from pydantic import Field
import mcp.types as types
import json
import sys

import asyncio

from fastmcp import FastMCP

from lassi.profiler import Timer
from lassi.compiler import Compiler, CompilerTool, CompilationError, COMPILER_FLAGS_DB
from lassi.source_file import SourceFile
from lassi.executer import FunctionalValidator, ExecTool
from lassi.profiler import MultiProfiler, CPUProfiler, GPUProfiler, ArmPowerProbe, NvidiaPowerProbe

# Initialize FastMCP server
mcp = FastMCP("LASSI") 


#============================================================================
#                                   TOOLS
#============================================================================

@mcp.tool()
async def compile_source(
    path: Annotated[str, Field(description="The absolute path to the source file to compile.")],
    compiler: Annotated[str, Field(description="The compiler to use (e.g. 'gcc', 'nvcc').")],
    kwds: Annotated[str, Field(description="Compiler flags (e.g. '-O3 -Wall').")] = None,
    output: Annotated[str, Field(description="The output binary file name.")] = None,
) -> str:
    """
    Compiles a source file using a specific compiler.
    """
    #print(f"Received compile_source request with path: {path}, compiler: {compiler}, kwds: {kwds}, output: {output}", file=sys.stderr)

    target_path = Path(path).resolve()
    output_path = Path(output).resolve() if output else None

    if not target_path.exists():
        return f"Compilation failed: File not found at {target_path}"

    # 3. Logic: Resolve the Compiler Enum
    try:
        compiler_tool = CompilerTool.from_string(compiler.lower())
            
    except ValueError as e:
        return f"Configuration Error: {str(e)}"

    # 4. Execution
    try:
        
        result_path = compiler_tool.compile(
            file=target_path,
            kwds=kwds,
            output_file=output_path
        )
        return f"Compilation successful. Binary created at: {result_path.name}"
    
    except Exception as e:
        return f"Compilation failed: {str(e)}"
    
@mcp.tool()
async def compile_to_mlir(
    path: Annotated[str, Field(description="The absolute path to the source file to compile.")],
    kwds: Annotated[str, Field(description="Specific flags for cgeist (e.g., '-function=*').")] = None,
    output: Annotated[str, Field(description="The output MLIR file name.")] = None,
) -> str:
    """
    Compiles a C/C++ source file specifically to MLIR using cgeist.
    """
    # 1. Resolve Input Paths
    target_path = Path(path).resolve()
    output_path = Path(output).resolve() if output else None

    # 2. Validation
    if not target_path.exists():
        return f"Compilation failed: File not found at {target_path}"

    try:
        # 3. Execution
        # We enforce CGEIST here. We do not ask the LLM to choose it.
        source_file = SourceFile(
            file_name=target_path, 
            compiler=Compiler.CGEIST
        )
        
        # We pass the arguments to the instance method
        result_path = source_file.compile(
            file=target_path,
            kwds=kwds,
            output_file=output_path
        )
        return f"MLIR generation successful. Output file: {result_path.name}"
    
    except Exception as e:
        return f"MLIR generation failed: {str(e)}"

@mcp.tool()
async def execute_with_latency(
    path: Annotated[str, Field(description="The absolute path to the executable binary.")],
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = ""
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

    try:
        # 1. Run the execution
        # Use asyncio.to_thread to run the blocking executer.run without stalling the event loop
        process_result = await asyncio.to_thread(executer.run, args=args)

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
    args: Annotated[str, Field(description="Command line arguments for the executable.")] = ""
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

    try:
        # 1. Run the execution
        # Use asyncio.to_thread to run the blocking executer.run without stalling the event loop
        process_result = await asyncio.to_thread(executer.run, args=args)

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

#============================================================================
#                               RESOURCES
#============================================================================

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