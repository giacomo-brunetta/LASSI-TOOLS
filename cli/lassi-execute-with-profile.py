#!/usr/bin/env python3
"""Run an executable, return its output and power profiling report."""
from __future__ import annotations
import argparse
import asyncio
from pathlib import Path
from _lassi_common import setup_path, run_async
setup_path()


async def _go(path: str, args: str, dump_output: str | None, expected_output: str | None) -> str:
    from lassi.core.executer import FunctionalValidator, ExecTool
    from lassi.profiling.profiler import (
        Timer, MultiProfiler, CPUProfiler, GPUProfiler, ArmPowerProbe, NvidiaPowerProbe,
    )
    target = Path(path).resolve()
    if not target.exists():
        return f"Execution failed: Executable not found at {target}"
    profilers: list = [Timer()]
    warnings: list[str] = []
    try:
        profilers.append(CPUProfiler(ArmPowerProbe()))
    except (FileNotFoundError, RuntimeError, OSError) as e:
        warnings.append(f"CPU power probe unavailable: {e}")
    try:
        profilers.append(GPUProfiler(NvidiaPowerProbe()))
    except (FileNotFoundError, RuntimeError, OSError) as e:
        warnings.append(f"GPU power probe unavailable: {e}")
    executer = ExecTool(executable=target, profiler=MultiProfiler(profilers))
    validator = FunctionalValidator(golden_output=expected_output) if expected_output else None
    try:
        proc = await asyncio.to_thread(executer.run, args=args, dump_output=dump_output, validator=validator)
        report = executer.get_last_execution_report()
        out: list[str] = []
        out.append(f"- **status**: {'success' if proc.returncode == 0 else 'failed'}")
        out.append(f"- **returncode**: {proc.returncode}")
        out.append(f"- **profile**: {report}")
        if warnings:
            out.append("")
            out.append("## Probe warnings")
            out.append("")
            for w in warnings:
                out.append(f"- {w}")
        if proc.stdout:
            out.append("")
            out.append("## Stdout")
            out.append("")
            out.append("```")
            out.append(proc.stdout.rstrip())
            out.append("```")
        if proc.stderr:
            out.append("")
            out.append("## Stderr")
            out.append("")
            out.append("```")
            out.append(proc.stderr.rstrip())
            out.append("```")
        return "\n".join(out)
    except Exception as e:
        return f"- **status**: error\n- **message**: {e}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--path", required=True, help="Absolute path to the executable binary.")
    p.add_argument("--args", default="", help="Command line arguments for the executable.")
    p.add_argument("--dump-output", default=None, help="Optional path to dump stdout.")
    p.add_argument("--expected-output", default=None, help="Optional path/string to compare output against.")
    a = p.parse_args()
    return run_async(_go(a.path, a.args, a.dump_output, a.expected_output), title="Execution + power profile")


if __name__ == "__main__":
    raise SystemExit(main())
