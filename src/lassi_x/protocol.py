"""Typed wire protocol for every LASSI-X process and network boundary.

This module is the single source of truth for messages that cross a process
boundary: the local Hermes worker JSONL protocol today, and the Academy-based
remote execution protocol (exec, file transfer, handshake) used to fan work
out to HPC resources.

Rules for every model defined here:

- Frozen and ``extra="forbid"`` so malformed or stale peers fail loudly.
- No ``pathlib.Path`` fields: remote paths are site-local, so messages carry
  workspace-relative POSIX strings validated by :func:`_validate_relative_path`.
- No credential material ever crosses the wire; messages carry only the names
  of environment variables to resolve on the executing side.
- ``schema_version`` is bumped only on incompatible changes, and both sides of
  a connection must pin the same ``lassi-x`` version.
"""

from __future__ import annotations

import posixpath
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    TypeAdapter,
    field_validator,
    model_validator,
)

PROTOCOL_VERSION = 1

MAX_INLINE_BYTES = 4 * 1024 * 1024
"""Largest payload allowed inline in a single message (file content, stdin)."""

MAX_TEXT_BYTES = 256 * 1024
"""Largest stdout/stderr excerpt returned inline; the remainder is spilled."""


class WireModel(BaseModel):
    """Base class for every message that crosses a process or network boundary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1


WorkspaceName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
"""Opaque workspace identifier; the executing side maps it to a confined directory."""


def _validate_relative_path(value: str) -> str:
    """Require a normalized, workspace-relative POSIX path.

    Args:
        value: Candidate path string from a wire message.

    Returns:
        The validated path, unchanged.

    Raises:
        ValueError: If the path is empty, absolute, escapes the workspace via
            ``..``, contains backslashes, or is not already normalized.

    """
    if not value:
        raise ValueError("path must not be empty")
    if "\\" in value:
        raise ValueError("path must use POSIX separators")
    if posixpath.isabs(value):
        raise ValueError("path must be workspace-relative, not absolute")
    normalized = posixpath.normpath(value)
    if normalized != value:
        raise ValueError(f"path must be normalized (expected {normalized!r})")
    if normalized == ".." or normalized.startswith("../"):
        raise ValueError("path must not escape the workspace")
    return value


# --------------------------------------------------------------------------
# Hermes worker protocol (local JSONL over stdin/stdout)
# --------------------------------------------------------------------------


class MemorySettings(BaseModel):
    """Mem0 memory-provider settings carried inside :class:`WorkerInit`.

    ``api_key_env`` names an environment variable resolved on the executing
    side; the credential itself never crosses the wire. It is optional because
    a self-hosted Mem0 server may run with authentication disabled.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str
    api_key_env: str | None = None
    user_id: str
    agent_id: str


class WorkerInit(WireModel):
    """Initialize one persistent Hermes agent inside a worker process.

    Credential fields name external sources only: ``api_key_env`` is resolved
    from the worker's own environment and ``claude_settings`` is a local
    settings file whose ``apiKeyHelper`` command produces the credential.
    A present ``memory`` field enables the external Mem0 memory provider for
    the agent; an absent one keeps every memory layer disabled.
    """

    op: Literal["init"] = "init"
    model: str
    provider: str | None = None
    base_url: str | None = None
    api_mode: Literal["chat_completions", "responses", "anthropic_messages"] | None = None
    reasoning_effort: (
        Literal["minimal", "low", "medium", "high", "xhigh", "max", "ultra"] | None
    ) = None
    api_key_env: str | None = None
    claude_settings: str | None = None
    max_tokens: int = Field(default=16_384, ge=256, le=131_072)
    max_iterations: int = Field(default=90, ge=1, le=500)
    system_prompt: str | None = None
    toolsets: list[str] = Field(default_factory=list)
    role: str
    memory: MemorySettings | None = None


class WorkerSend(WireModel):
    """Deliver one user prompt to the initialized agent conversation."""

    op: Literal["send"] = "send"
    prompt: str


class WorkerClose(WireModel):
    """Request a graceful worker shutdown."""

    op: Literal["close"] = "close"


WorkerRequest = Annotated[WorkerInit | WorkerSend | WorkerClose, Field(discriminator="op")]

_worker_request_adapter: TypeAdapter[WorkerRequest] = TypeAdapter(WorkerRequest)


class TurnUsage(WireModel):
    """Token and estimated-cost delta attributed to one conversation turn."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)


class WorkerReady(WireModel):
    """Acknowledge successful worker initialization."""

    kind: Literal["ready"] = "ready"


class WorkerTurn(WireModel):
    """Return the final agent text and usage delta for one send operation."""

    kind: Literal["turn"] = "turn"
    text: str
    usage: TurnUsage
    completed: bool = True
    exit_reason: str = "unknown"


class WorkerFailure(WireModel):
    """Report a worker-side error while keeping the protocol stream alive."""

    kind: Literal["error"] = "error"
    error: str
    traceback: str = ""
    usage: TurnUsage = Field(default_factory=TurnUsage)


WorkerResponse = Annotated[WorkerReady | WorkerTurn | WorkerFailure, Field(discriminator="kind")]

_worker_response_adapter: TypeAdapter[WorkerResponse] = TypeAdapter(WorkerResponse)


def parse_worker_request(line: str | bytes) -> WorkerRequest:
    """Decode and validate one worker request line.

    Args:
        line: Raw JSONL request read from the protocol stream.

    Returns:
        The validated request message.

    Raises:
        pydantic.ValidationError: If the line is not a valid worker request.

    """
    return _worker_request_adapter.validate_json(line)


def parse_worker_response(line: str | bytes) -> WorkerResponse:
    """Decode and validate one worker response line.

    Args:
        line: Raw JSONL response read from the protocol stream.

    Returns:
        The validated response message.

    Raises:
        pydantic.ValidationError: If the line is not a valid worker response.

    """
    return _worker_response_adapter.validate_json(line)


# --------------------------------------------------------------------------
# Remote execution protocol (Academy actions between harness and HPC agents)
# --------------------------------------------------------------------------


class ExecRequest(WireModel):
    """Execute one argv command inside a confined remote workspace.

    ``env`` sets explicit, non-secret variables (for example ``OMP_NUM_THREADS``);
    secrets must live in the executing side's own environment and are never
    accepted on the wire.
    """

    workspace: WorkspaceName
    argv: list[str] = Field(min_length=1)
    cwd: str | None = None
    stdin_text: str | None = Field(default=None, max_length=MAX_INLINE_BYTES)
    timeout_s: float = Field(default=600.0, gt=0.0, le=24 * 3600.0)
    env: dict[str, str] = Field(default_factory=dict)

    @field_validator("cwd")
    @classmethod
    def cwd_is_relative(cls, value: str | None) -> str | None:
        """Confine the working directory to the workspace."""
        return None if value is None else _validate_relative_path(value)

    @field_validator("argv")
    @classmethod
    def argv_entries_nonempty(cls, value: list[str]) -> list[str]:
        """Reject empty argv entries that would confuse exec semantics."""
        if not value[0]:
            raise ValueError("argv[0] must not be empty")
        return value


class ExecResult(WireModel):
    """Outcome of one remote command execution."""

    workspace: WorkspaceName
    exit_code: int | None = None
    timed_out: bool = False
    stdout: str = Field(default="", max_length=MAX_TEXT_BYTES)
    stderr: str = Field(default="", max_length=MAX_TEXT_BYTES)
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    duration_s: float = Field(ge=0.0)

    @property
    def ok(self) -> bool:
        """Whether the command completed within its deadline and exited zero."""
        return self.exit_code == 0 and not self.timed_out


class FilePut(WireModel):
    """Write one file into a remote workspace.

    Exactly one of ``text`` or ``content_b64`` carries the payload. ``sha256``
    optionally lets the receiver verify integrity after decoding.
    """

    workspace: WorkspaceName
    path: str
    text: str | None = Field(default=None, max_length=MAX_INLINE_BYTES)
    content_b64: str | None = Field(default=None, max_length=2 * MAX_INLINE_BYTES)
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    make_parents: bool = True
    executable: bool = False

    @field_validator("path")
    @classmethod
    def path_is_relative(cls, value: str) -> str:
        """Confine the destination to the workspace."""
        return _validate_relative_path(value)

    @model_validator(mode="after")
    def exactly_one_payload(self) -> FilePut:
        """Require exactly one payload representation."""
        if (self.text is None) == (self.content_b64 is None):
            raise ValueError("provide exactly one of text or content_b64")
        return self


class FileStat(WireModel):
    """Acknowledgment for a completed :class:`FilePut` write."""

    workspace: WorkspaceName
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)


class FileGet(WireModel):
    """Read one file (or one chunk of it) from a remote workspace.

    Files larger than ``max_bytes`` are fetched in chunks by advancing
    ``offset`` until the response is no longer ``truncated``.
    """

    workspace: WorkspaceName
    path: str
    offset: int = Field(default=0, ge=0)
    max_bytes: int = Field(default=MAX_INLINE_BYTES, ge=1, le=MAX_INLINE_BYTES)

    @field_validator("path")
    @classmethod
    def path_is_relative(cls, value: str) -> str:
        """Confine the source to the workspace."""
        return _validate_relative_path(value)


class FileContent(WireModel):
    """File payload returned for a :class:`FileGet` request.

    ``encoding`` is ``utf-8`` when ``content`` is the decoded text and
    ``base64`` when the file is binary or not valid UTF-8.
    """

    workspace: WorkspaceName
    path: str
    encoding: Literal["utf-8", "base64"]
    content: str = Field(max_length=2 * MAX_INLINE_BYTES)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    truncated: bool = False


class DirEntry(WireModel):
    """One entry of a remote directory listing."""

    name: str
    kind: Literal["file", "dir", "other"]
    size_bytes: int | None = None


class ListDir(WireModel):
    """List one directory inside a remote workspace."""

    workspace: WorkspaceName
    path: str = "."

    @field_validator("path")
    @classmethod
    def path_is_relative(cls, value: str) -> str:
        """Confine the listing to the workspace."""
        return _validate_relative_path(value)


class DirListing(WireModel):
    """Directory entries returned for a :class:`ListDir` request."""

    workspace: WorkspaceName
    path: str
    entries: list[DirEntry] = Field(default_factory=list)


class AcceleratorInfo(WireModel):
    """One accelerator device visible to a remote execution agent."""

    kind: str
    name: str
    index: int = Field(default=0, ge=0)
    total_memory_mb: int | None = Field(default=None, ge=0)


class HandshakeReport(WireModel):
    """Measured capabilities of one remote execution agent.

    Produced at agent startup and recorded into run provenance, so advertised
    capabilities are always observed on the executing host rather than declared
    in configuration.
    """

    resource: str | None = None
    hostname: str
    platform: str
    python_version: str
    python_executable: str
    lassi_x_version: str
    torch_version: str | None = None
    accelerators: list[AcceleratorInfo] = Field(default_factory=list)
    toolchain: dict[str, str] = Field(default_factory=dict)
    workspace_root: str
