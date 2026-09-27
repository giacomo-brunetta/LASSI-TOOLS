"""Observe only container capabilities, without loading the orchestration stack."""

import platform
import socket
import subprocess
import sys

import torch

from lassi_x import __version__
from lassi_x.protocol import HandshakeReport

print(
    HandshakeReport(
        hostname=socket.gethostname(),
        platform=platform.platform(),
        python_version=platform.python_version(),
        python_executable=sys.executable,
        lassi_x_version=__version__,
        torch_version=torch.__version__,
        workspace_root="/workspace",
        toolchain={"gcc": subprocess.check_output(["gcc", "--version"], text=True).splitlines()[0]},
    ).model_dump_json()
)
