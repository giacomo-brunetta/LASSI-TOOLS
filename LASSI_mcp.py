from typing import Any
from pathlib import Path

import asyncio 

from fastmcp import FastMCP

from lassi.profiler import Timer, MultiProfiler, GPUProfiler, CPUProfiler
from lassi.source_file import SourceFile
from lassi.executer import FunctionalValidator

profiler = MultiProfiler([GPUProfiler(), CPUProfiler()])

# Initialize FastMCP server
mcp = FastMCP("LASSI") 

@mcp.tool()
async def file_name(path : Path) -> str:
    """Read the filename of the source file."""
    source_file = SourceFile(file_name = path)
    return str(source_file.file_name)

@mcp.tool()
async def read(path : Path) -> str:
    """Read the content of the source file."""
    source_file = SourceFile(file_name = path)
    return source_file.read()

@mcp.tool()
async def compile(path : Path) -> str:
    """Compile the source file."""
    source_file = SourceFile(file_name = path)
    try: 
        source_file.compile()
        return "Compilation successful."
    except Exception as e:
        return f"Compilation failed: {str(e)}"
    
@mcp.tool()
async def compile_to_MLIR(path : Path) -> str:
    """Compile the source file."""
    source_file = SourceFile(file_name = path)
    try: 
        source_file.compile()
        return "Compilation successful."
    except Exception as e:
        return f"Compilation failed: {str(e)}"

@mcp.tool()
async def execute(path : Path) -> str:
    """Execute the compiled source file with profiling."""
    source_file = SourceFile(file_name = path)
    try:
        report = source_file.execute(profiler=profiler)
        return f"Execution successful. Report: {report}"
    except Exception as e:
        return f"Execution failed: {str(e)}"

def main():
    # Initialize and run the server
    mcp.run(transport="http", host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()