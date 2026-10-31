"""Typed reconstruction of persisted dataclasses at JSON boundaries."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from pydantic import TypeAdapter


@lru_cache
def _adapter(cls: type[Any]) -> TypeAdapter[Any]:
    adapter = TypeAdapter(cls)
    # Lightweight runtime modules defer pathlib imports for measurement workers.
    adapter.rebuild(_types_namespace={"Path": Path})
    return adapter


def restore_record[RecordT](cls: type[RecordT], value: dict[str, Any]) -> RecordT:
    """Validate nested records strictly while allowing JSON paths and enum values."""
    return cast("RecordT", _adapter(cast("Any", cls)).validate_json(json.dumps(value), strict=True))
