import shlex
from pathlib import Path
from typing import Callable, Optional, Tuple, Type, List
from lassi.utils import *
from lassi.profiler import Profiler, Timer, Report

class WrongRetCode(Exception):
    pass

class WrongOutput(Exception):
    pass

class FunctionalValidator:
    
    def __init__(
        self,
        args : str = "",
        golden_output : str | Path = None,
        ret_code : int = 0
    ):
        self.args = args
        self.golden_output = golden_output
        self.ret_code = ret_code

    def validate(self, program_output: subprocess.CompletedProcess):
        if program_output.returncode != self.ret_code:
            raise WrongRetCode(f"Wrong return code.\nExpected {self.ret_code}, received {program_output.returncode}")
        
        if self.golden_output:
            # If golden_output is a path, read its content for comparison
            expected = self.golden_output
            if isinstance(self.golden_output, Path) or (isinstance(self.golden_output, str) and Path(self.golden_output).exists()):
                expected = Path(self.golden_output).read_text()

            if expected != program_output.stdout:
                raise WrongOutput(f"Wrong output.\nExpected output does not match received stdout.")
        
        return True

class ExecTool:
    """
    A tool for running an executable, optionally wrapped by a Profiler.

    The profiler is expected to implement:

        profile_task(self, f: Callable[[], subprocess.CompletedProcess])
            -> tuple[subprocess.CompletedProcess, Report]
    """

    def __init__(
        self,
        executable: Path,
        arguments: str = "",
        profiler: Optional[Type[Profiler]] = Timer(),
    ) -> None:
        # Normalize path so we never need "./"
        self.executable: Path = (
            executable.resolve()
        )
        
        if isinstance(arguments, (list, tuple, set)):
            arguments = " ".join(str(x) for x in arguments)
        elif not isinstance(arguments, str):
            raise TypeError("arguments must be a string or iterable of strings/numbers")
        else:
            self.args = arguments

        self.profiler = profiler

        self.report_history = []

    def __repr__(self) -> str:
        profiler_repr = self.profiler.__class__.__name__ if self.profiler else None
        return (
            f"ExecTool(\n"
            f"  executable={self.executable!r},\n"
            f"  args={self.args!r},\n"
            f"  profiler={profiler_repr!r}\n"
            f")"
        )

    def run(
        self,
        args: str = None,
        profiler: Profiler = None,
        validator: FunctionalValidator = None,
        dump_output: str | Path = None
    ) -> subprocess.CompletedProcess:
        
        if args:
            pass # args is already set
        elif validator:
            args = validator.args
        else:
            args = self.args

        # FIX 1: Wrap map() in list(). 
        # Without this, 'cmd' is an iterator that gets exhausted by the print statement below.
        cmd = list(map(str, [str(self.executable.resolve()), *shlex.split(args)]))

        # FIX 2: Redirect logs to stderr. 
        # Regular print() writes to stdout, which corrupts the MCP JSON-RPC protocol.
        print(f"Running with command: {' '.join(cmd)}", file=sys.stderr)

        # Use provided profiler if available, otherwise fallback to default
        active_profiler = profiler if profiler is not None else self.profiler

        if active_profiler is not None:
            completed_process, report = active_profiler.profile_task(
                f = lambda: stdio_safe_subprocess_run(cmd, timeout=300)
            )
            self.report_history.append(report)
        else:
            # Note: Ensure stdio_safe_subprocess_run handles capture_output internally
            # as defined in our previous step.
            completed_process = stdio_safe_subprocess_run(cmd)

        if dump_output:
            dump_path = Path(dump_output).resolve()
            print(f"Dumping output to: {dump_path}", file=sys.stderr)
            dump_path.write_text(completed_process.stdout)

        if validator:
            print("Validating output", file=sys.stderr) # FIX 3: Safe logging
            validator.validate(completed_process)

        return completed_process
        
    def get_last_execution_report(self) -> Report:
        return self.report_history[-1]
    
    def get_execution_history(self) -> List[Report]:
        return self.report_history