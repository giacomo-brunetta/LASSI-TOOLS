from pathlib import Path
from lassi.executer import ExecTool
from lassi.profiler import MultiProfiler, Timer, CPUProfiler, GPUProfiler, ArmPowerProbe, NvidiaPowerProbe

executables = [
    "matmul_O1",
    "matmul_O2",
    "matmul_O3",
    "matmul_Ofast"
]

base_path = Path("/home/gbrun/TEST")

for exe_name in executables:
    target_path = (base_path / exe_name).resolve()
    executer = ExecTool(
        executable=target_path,
        profiler=MultiProfiler([
                    Timer(),
                    CPUProfiler(ArmPowerProbe()),
                    GPUProfiler(NvidiaPowerProbe())]
            )
        )
    
    print(f"--- Profiling {exe_name} ---")
    process_result = executer.run(args="1000 1000 1000")
    report = executer.get_last_execution_report()
    
    if process_result.returncode == 0:
        print(f"Status: Success")
        print(f"Report: {report}")
    else:
        print(f"Status: Failed (Code {process_result.returncode})")
        print(f"Stderr: {process_result.stderr}")
    print("\n")
