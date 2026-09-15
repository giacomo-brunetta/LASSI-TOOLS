"""Tests for remote subprocess lifecycle behavior."""

import asyncio
import sys
from pathlib import Path

from lassi_x.execution.local import LocalExecutionBackend
from lassi_x.protocol import ExecRequest


def test_execute_timeout_kills_shell_children_holding_pipes(tmp_path: Path) -> None:
    """A timed-out shell must not leave a child keeping communicate() open."""
    backend = LocalExecutionBackend(tmp_path)
    request = ExecRequest(
        workspace="c1",
        argv=["/bin/sh", "-c", '"$PYTHON" -c "import time; time.sleep(60)" & wait'],
        timeout_s=0.2,
        env={"PYTHON": sys.executable},
    )
    result = asyncio.run(backend.execute(request))
    assert result.timed_out
    assert result.exit_code is None
    assert result.duration_s < 10
