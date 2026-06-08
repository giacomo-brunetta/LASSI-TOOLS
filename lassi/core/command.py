from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


def merged_env(environment: dict[str, Any] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    for key, value in (environment or {}).items():
        env[str(key)] = str(value)
    return env


def run_command(
    cmd: list[str],
    *,
    cwd: str | Path | None = None,
    env: dict[str, Any] | None = None,
    timeout_s: int | float = 60,
    merge_env: bool = True,
) -> subprocess.CompletedProcess[str]:
    effective_env = merged_env(env) if merge_env else env
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=effective_env,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def run_shell_command(
    command: str,
    shell: str = "bash",
    *,
    cwd: str | Path | None = None,
    env: dict[str, Any] | None = None,
    timeout_s: int | float = 60,
    merge_env: bool = True,
) -> subprocess.CompletedProcess[str]:
    return run_command(
        [shell, "-lc", command],
        cwd=cwd,
        env=env,
        timeout_s=timeout_s,
        merge_env=merge_env,
    )
