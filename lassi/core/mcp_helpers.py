"""Shared helpers used by multiple MCP tool implementations.

These were duplicated across ``lassi.profiling.performance_tools`` and
``lassi.verification.verification_tools``. Only helpers that are byte-for-byte
identical in both modules are factored here. Verdict-shaping helpers like
``_json_response`` and process runners like ``_run_command`` differ between
modules (different verdict sets, env-merging behavior, default timeouts) and
intentionally remain local to each tool module.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def now_task_id(prefix: str) -> str:
    """Return a unique task identifier of the form ``<prefix>_<YYYYmmdd_HHMMSS>_<pid>``."""
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"


def short(text: str | None, limit: int = 20000) -> str:
    """Return ``text`` truncated to ``limit`` bytes with a truncation marker."""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... truncated {len(text) - limit} bytes ..."


def write_json(path: Path, data: Any) -> Path:
    """Write ``data`` as pretty JSON to ``path``, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path
