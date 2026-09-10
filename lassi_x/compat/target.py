"""Machine-target configuration and compiler-checker loading."""

from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, cast

import yaml

from lassi_x.compat.fixtures import PRECISION_DTYPES

TARGET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def load_target(path: str | Path) -> dict[str, Any]:
    target_path = Path(path)
    if target_path.is_dir():
        target_path = target_path / "target.yaml"
    payload = yaml.safe_load(target_path.read_text(encoding="utf-8")) or {}
    required = ("schema_version", "target_id", "family", "checker", "precisions")
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError("target config is missing: " + ", ".join(missing))
    if payload["schema_version"] != 1:
        raise ValueError("unsupported target schema_version")
    if not TARGET_ID_RE.fullmatch(str(payload["target_id"])):
        raise ValueError("target_id must contain only lowercase letters, digits, '.', '_' or '-'")
    precisions = payload["precisions"]
    if not isinstance(precisions, list) or not precisions:
        raise ValueError("target precisions must be a non-empty list")
    unknown = sorted(set(precisions) - set(PRECISION_DTYPES))
    if unknown:
        raise ValueError("unknown target precisions: " + ", ".join(unknown))
    payload.setdefault("timeout_s", 300.0)
    payload.setdefault("max_workers", 1)
    payload.setdefault("options", {})
    if float(payload["timeout_s"]) <= 0 or int(payload["max_workers"]) <= 0:
        raise ValueError("target timeout_s and max_workers must be positive")
    payload["config_path"] = str(target_path.resolve())
    return payload


def checker_class(target: dict[str, Any]) -> type[Any]:
    module_name, separator, attribute = str(target["checker"]).partition(":")
    if not separator:
        raise ValueError("target checker must use module:Class syntax")
    module = importlib.import_module(module_name)
    checker = getattr(module, attribute)
    return cast("type[Any]", checker)
