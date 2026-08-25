"""Unified compatibility database helpers and query API."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from compat_tool.utils import (
    DEFAULT_ALL_OPS_PATH,
    DEFAULT_COMPATIBILITY_PATH,
    DEFAULT_DB_PATH,
    load_json,
    save_json,
    select_recommended_alternative,
)


def build_db(all_ops_path: str | Path, compatibility_path: str | Path) -> dict[str, dict[str, Any]]:
    """Merge parsed ops and compatibility results into a single database."""
    all_ops = load_json(all_ops_path, default={})
    compatibility = load_json(compatibility_path, default={})

    db: dict[str, dict[str, Any]] = {}
    for op_name in sorted(all_ops):
        compat_info = compatibility.get(op_name, {})
        db[op_name] = {
            "supported": bool(compat_info.get("supported", False)),
            "tosa_op": compat_info.get("tosa_op"),
            "error": compat_info.get("error"),
            "attempts": compat_info.get("attempts", {}),
            "supported_profiles": compat_info.get("supported_profiles", []),
            "range_restriction": compat_info.get("range_restriction"),
            "dtype_notes": compat_info.get("dtype_notes", []),
        }

    for op_name, info in db.items():
        info["recommended_alternative"] = None
        if not info.get("supported"):
            info["recommended_alternative"] = select_recommended_alternative(op_name, db)

    save_json(DEFAULT_DB_PATH, db)
    return db


def _load_db(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, dict[str, Any]]:
    """Load the compatibility database from disk."""
    return load_json(db_path, default={})


def is_supported(op_name: str, db_path: str | Path = DEFAULT_DB_PATH) -> bool:
    """Return whether an op is marked as TOSA-compatible."""
    return bool(_load_db(db_path).get(op_name, {}).get("supported", False))


def get_op_info(op_name: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Return the database entry for an op, or an empty unsupported record."""
    return _load_db(db_path).get(op_name, {"supported": False, "tosa_op": None, "error": "Unknown op"})


def validate_ops(op_list: list[str], db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, list[str]]:
    """Split a list of ops into supported and unsupported groups."""
    database = _load_db(db_path)
    supported: list[str] = []
    unsupported: list[str] = []

    for op_name in op_list:
        if database.get(op_name, {}).get("supported", False):
            supported.append(op_name)
        else:
            unsupported.append(op_name)

    return {"supported": supported, "unsupported": unsupported}
