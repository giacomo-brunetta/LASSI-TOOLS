import subprocess
import shlex
from pathlib import Path
from typing import Callable, Optional, Tuple, Type

from lassi.profiler import Profiler, Timer, Report


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
        self.args: str = arguments

        self.profiler = profiler

    def __repr__(self) -> str:
        profiler_repr = self.profiler.__class__.__name__ if self.profiler else None
        return (
            f"ExecTool(\n"
            f"  executable={self.executable!r},\n"
            f"  args={self.args!r},\n"
            f"  profiler={profiler_repr!r}\n"
            f")"
        )

    def run(self, profiler : Profiler = None) -> Tuple[subprocess.CompletedProcess, Optional[Report]]:

        # Build command; subprocess accepts Path objects in recent Python versions
        cmd = [self.executable, *shlex.split(self.args)]

        print(f"Running with command: {' '.join(map(str, cmd))}")

        if profiler is None:
            completed_process, report = self.profiler.profile_task(
                f = lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            return completed_process, report
        else:
            completed_process, report = profiler.profile_task(
                f = lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            return completed_process, report
