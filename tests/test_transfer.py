"""Tests for bounded remote workspace transfers."""

from __future__ import annotations

import asyncio
import base64
from typing import TYPE_CHECKING

from lassi_x.execution import LocalExecutionBackend, fetch_bytes
from lassi_x.execution.transfer import TRANSFER_CHUNK_BYTES
from lassi_x.protocol import FilePut

if TYPE_CHECKING:
    from pathlib import Path


def test_fetch_bytes_uses_sse_safe_default_chunk_size(tmp_path: Path) -> None:
    """The default download must span messages instead of one large SSE line."""
    backend = LocalExecutionBackend(tmp_path)
    payload = bytes(range(256)) * (TRANSFER_CHUNK_BYTES // 256 + 2) + b"tail"
    asyncio.run(
        backend.put_file(
            FilePut(
                workspace="c1",
                path="large.bin",
                content_b64=base64.b64encode(payload).decode(),
            )
        )
    )

    assert asyncio.run(fetch_bytes(backend, "c1", "large.bin")) == payload
