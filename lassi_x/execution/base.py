"""Abstract workspace execution interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..protocol import (
        DirListing,
        ExecRequest,
        ExecResult,
        FileContent,
        FileGet,
        FilePut,
        FileStat,
        HandshakeReport,
        ListDir,
    )

class ExecutionBackend(ABC):
    """Workspace-confined execution and file operations on one resource."""

    _cached_handshake: HandshakeReport | None = None

    @abstractmethod
    async def execute(self, request: ExecRequest) -> ExecResult:
        """Execute one argv command inside its confined workspace."""

    @abstractmethod
    async def put_file(self, request: FilePut) -> FileStat:
        """Write one file into its confined workspace."""

    @abstractmethod
    async def get_file(self, request: FileGet) -> FileContent:
        """Read one file from its confined workspace."""

    @abstractmethod
    async def list_dir(self, request: ListDir) -> DirListing:
        """List one directory inside its confined workspace."""

    @abstractmethod
    async def handshake(self) -> HandshakeReport:
        """Measure and report the executing host's capabilities."""

    async def ping(self) -> None:  # noqa: B027 -- no-op by design, not abstract
        """Prove the backend still answers.

        A backend that runs in this process cannot stop answering without the
        process itself stopping, so the default is a no-op and only the remote
        backend does real work here.
        """

    async def start_keepalive(self) -> None:  # noqa: B027 -- see ping
        """Begin probing liveness, if this backend can lose contact at all."""

    async def stop_keepalive(self) -> None:  # noqa: B027 -- see ping
        """Stop probing liveness and release the probe task."""

    async def cached_handshake(self) -> HandshakeReport:
        """Return the handshake, measuring it at most once per backend.

        Returns:
            The measured or previously cached handshake report.

        """
        if self._cached_handshake is None:
            self._cached_handshake = await self.handshake()
        return self._cached_handshake
