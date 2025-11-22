import subprocess
import shlex
from pathlib import Path
from typing import Callable, Optional, Tuple, Type, List

from lassi.profiler import Profiler, Timer, Report

class WrongRetCode(Exception):
    pass

class WrongOutput(Exception):
    pass

class FunctionalValidator:
    
    def __init__(self, args : str = "", golden_output : str | Path = None, ret_code : int = 0):
        self.args = args
        self.golden_output = golden_output
        self.ret_code = ret_code

    def validate(self, program_output: subprocess.CompletedProcess):
        if program_output.returncode != self.ret_code:
            raise WrongRetCode(f"Wrong return code.\nExpected {self.ret_code}, received {program_output.returncode}")
        
        if self.golden_output and self.golden_output != program_output.stdout:
            raise WrongOutput(f"Wrong output.\nExpected {self.golden_output}, received {program_output.stdout}")
        
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

    def run(self, args : str = None, profiler : Profiler = None, validator : FunctionalValidator = None) -> subprocess.CompletedProcess:

        if args:
            args = args
        elif validator:
            args = validator.args
        else:
            args = self.args

        # Build command; subprocess accepts Path objects in recent Python versions
        cmd = [self.executable, *shlex.split(args)]

        print(f"Running with command: {' '.join(map(str, cmd))}")

        if profiler is None:
            completed_process, report = self.profiler.profile_task(
                f = lambda: subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True)
            )
            self.report_history.append(report)

        else:
            completed_process, report = profiler.profile_task(
                f = lambda: subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True)
            )

        if validator:
            print("Validating output")
            validator.validate(completed_process)

        return completed_process
        
    def get_last_execution_report(self) -> Report:
        return self.report_history[-1]
    
    def get_execution_history(self) -> List[Report]:
        return self.report_history
