"""Lightweight JSON, hashing, and atomic-write helpers.

This module deliberately does not import PyTorch so wiki queries work in a
documentation-only environment.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA_DIR = PACKAGE_ROOT / "data"
WIKI_DIR = PACKAGE_ROOT / "wiki"
SNAPSHOT_DIR = PACKAGE_ROOT / "snapshots"
TARGET_DIR = PACKAGE_ROOT / "targets"
DEFAULT_DB_PATH = DATA_DIR / "compat_db.json"


def load_json(path: str | Path, default: Any | None = None) -> Any:
    json_path = Path(path)
    if not json_path.exists():
        return {} if default is None else default
    with json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_json(path: str | Path, data: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, destination)


def stable_hash(data: Any) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
