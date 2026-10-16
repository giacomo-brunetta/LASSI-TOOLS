"""Recognize provider interruptions separately from scientific failures."""

from __future__ import annotations

import json
from typing import Any


def model_service_interrupted(value: Any) -> bool:
    text = json.dumps(value).lower()
    return any(
        marker in text
        for marker in (
            "usage limit has been reached",
            "insufficient_quota",
            "rate_limit_exceeded",
            "quota exceeded",
            "http 429",
            "http 401",
            "http 403",
        )
    )
