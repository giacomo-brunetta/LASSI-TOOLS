from typing import Annotated
from pathlib import Path
from pydantic import Field
import mcp.types as types
import json
import sys

import asyncio 

from lassi.profiler import Timer
from lassi.compiler import Compiler, CompilerTool, CompilationError, COMPILER_FLAGS_DB
from lassi.source_file import SourceFile
from lassi.executer import FunctionalValidator, ExecTool
from lassi.profiler import MultiProfiler, CPUProfiler, GPUProfiler, ArmPowerProbe, NvidiaPowerProbe


target_path = Path("/home/gbrun/TEST/matmul_Ofast").resolve()
executer = ExecTool(
    executable=target_path,
    profiler=MultiProfiler([
                Timer(),
                CPUProfiler(ArmPowerProbe()),
                GPUProfiler(NvidiaPowerProbe())]
        )
    )

# 1. Run the execution
# The run method returns a subprocess.CompletedProcess object
process_result = executer.run(args="1000 1000 1000")

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

print("\n".join(output_parts))

report = executer.get_last_execution_report()

print("Execution Report:")
print(report)