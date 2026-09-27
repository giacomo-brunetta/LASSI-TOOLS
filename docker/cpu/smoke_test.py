"""Real Docker integration check; no LLM calls or accelerator allocation."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import numpy as np

from lassi_x.config import DockerExecutionConfig
from lassi_x.execution.docker import DockerExecutionBackend
from lassi_x.protocol import ExecRequest, FilePut

CANDIDATE = """
from pathlib import Path
import torch
def build_inputs(device, dtype):
    return (torch.arange(8, device=device, dtype=dtype),)
class Model(torch.nn.Module):
    def forward(self, x):
        try:
            Path(__file__).write_text("must not work")
        except OSError:
            pass
        else:
            raise RuntimeError("candidate code was writable during validation")
        return x * 2
def make_model():
    return Model()
"""


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="lassi-docker-smoke-") as directory:
        root = Path(directory)
        backend = DockerExecutionBackend(root, DockerExecutionConfig())
        report = await backend.handshake()
        assert not report.accelerators
        print(f"Container runtime: Python {report.python_version}, Torch {report.torch_version}")
        await backend.put_file(FilePut(workspace="c1", path="candidate.py", text=CANDIDATE))
        result = await backend.execute(
            ExecRequest(
                workspace="c1",
                argv=[
                    report.python_executable,
                    "-m",
                    "lassi_x.runner",
                    "--module",
                    "candidate.py",
                    "--device",
                    "cpu",
                    "--precision",
                    "fp64",
                    "--output",
                    ".lassi/output.npy",
                ],
            )
        )
        assert result.ok, result.stderr or result.stdout
        np.testing.assert_array_equal(np.load(root / "c1/.lassi/output.npy"), np.arange(8) * 2)
        print("FP64 candidate output and read-only code: OK")
        for code in [
            "from pathlib import Path; Path('/tmp/marker').write_text('first')",
            "from pathlib import Path; assert not Path('/tmp/marker').exists()",
        ]:
            result = await backend.execute(
                ExecRequest(workspace="c1", argv=[report.python_executable, "-c", code])
            )
            assert result.ok, result.stderr
        print("Fresh temporary filesystem per invocation: OK")
        result = await backend.execute(
            ExecRequest(
                workspace="c1",
                argv=[report.python_executable, "-c", "import time; time.sleep(30)"],
                timeout_s=2,
            )
        )
        assert result.timed_out
        print("Timeout and explicit container cleanup: OK")


if __name__ == "__main__":
    asyncio.run(main())
