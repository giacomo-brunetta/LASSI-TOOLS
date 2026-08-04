"""End-to-end checks against a running self-hosted Mem0 server.

These tests exercise the exact HTTP backend the Hermes mem0 plugin uses at
run time (``plugins.memory.mem0._backend.SelfHostedBackend``), so a passing
run proves the ``docker/mem0`` stack speaks the contract agents depend on.
They are skipped automatically when no server is reachable; start one with
``docker compose -f docker/mem0/compose.yaml up -d`` first.
"""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING, Any

import httpx
import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

pytestmark = pytest.mark.mem0

HOST = os.environ.get("LASSI_X_MEM0_HOST", "http://localhost:8888")


def _server_available() -> bool:
    try:
        response = httpx.get(f"{HOST}/docs", timeout=2.0, follow_redirects=True)
    except httpx.HTTPError:
        return False
    return response.status_code == 200


@pytest.fixture(scope="module")
def backend() -> Iterator[Any]:
    if not _server_available():
        pytest.skip(f"no Mem0 server reachable at {HOST} (start docker/mem0)")
    from plugins.memory.mem0._backend import SelfHostedBackend  # noqa: PLC0415

    client = SelfHostedBackend(os.environ.get("MEM0_API_KEY", ""), HOST)
    yield client
    client.close()


def test_memory_round_trip_through_hermes_backend(backend: Any) -> None:
    user_id = f"lassi-x-test-{uuid.uuid4().hex[:8]}"
    fact = "LASSI-X probe: pairwise summation halved the fp16 error on 3mm."
    created = backend.add(
        [{"role": "user", "content": fact}],
        user_id=user_id,
        agent_id="c1",
        infer=False,
    )
    results = created.get("results") if isinstance(created, dict) else None
    assert results, f"server stored no memory: {created!r}"
    memory_id = results[0]["id"]
    try:
        found = backend.search("fp16 summation error", filters={"user_id": user_id}, top_k=5)
        assert any(entry.get("id") == memory_id for entry in found), found
    finally:
        backend.delete(memory_id)
