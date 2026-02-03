import argparse
import sys
import asyncio
from pathlib import Path
from lassi.profiler import Timer
from lassi.executer import ExecTool, FunctionalValidator

async def run_execution():
    parser = argparse.ArgumentParser(description="Run an executable and measure latency.")
    parser.add_argument("--path", required=True, help="Path to the executable.")
    parser.add_argument("--args", default="", help="Command line arguments.")
    parser.add_argument("--dump_output", help="Optional path to dump stdout.")
    parser.add_argument("--expected_output", help="Optional path/string for validation.")

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    if not target_path.exists():
        print(f"Execution failed: Executable not found at {target_path}")
        sys.exit(1)

    executer = ExecTool(executable=target_path, profiler=Timer())
    validator = FunctionalValidator(golden_output=args.expected_output) if args.expected_output else None

    try:
        process_result = await asyncio.to_thread(executer.run, args=args.args, dump_output=args.dump_output, validator=validator)
        report = executer.get_last_execution_report()

        status = "Success" if process_result.returncode == 0 else f"Failed (Code {process_result.returncode})"
        print(f"--- Execution {status} ---")
        print(f"Profile Report: {report}")

        if process_result.stdout:
            print("\n--- Stdout ---")
            print(process_result.stdout.strip())
            
        if process_result.stderr:
            print("\n--- Stderr ---")
            print(process_result.stderr.strip())

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_execution())
