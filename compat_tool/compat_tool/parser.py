"""Parsing for Torch MLIR TableGen operation definitions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from compat_tool.utils import DEFAULT_ALL_OPS_PATH, save_json


OP_BLOCK_RE = re.compile(
    r"def\s+(?P<def_name>\w+)\s*:\s*Torch_Op<\"(?P<op_name>[^\"]+)\".*?>\s*\{(?P<body>.*?)^\}",
    re.DOTALL | re.MULTILINE,
)
SECTION_RE_TEMPLATE = r"let\s+{section}\s*=\s*\((?:ins|outs)\s*(?P<content>.*?)\);"
ARG_RE = re.compile(r"(?P<type>[\w\[\]\.?]+):\$(?P<name>[\w]+)")


def _extract_section(body: str, section: str) -> list[dict[str, str]]:
    """Extract TableGen argument or result entries from one op body."""
    pattern = re.compile(SECTION_RE_TEMPLATE.format(section=section), re.DOTALL | re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return []

    entries: list[dict[str, str]] = []
    for entry in ARG_RE.finditer(match.group("content")):
        entries.append({"name": entry.group("name"), "type": entry.group("type")})
    return entries


def _is_private_or_internal(op_name: str) -> bool:
    """Filter out non-public or internal ops."""
    if not op_name.startswith("aten."):
        return True
    suffix = op_name.split(".", maxsplit=1)[1]
    return suffix.startswith("_")


def parse_torch_ops(td_file: str) -> dict[str, dict[str, Any]]:
    """
    Parse a Torch MLIR TableGen file into op metadata.

    Returns a mapping like:
    {
        "aten.relu": {
            "mlir_name": "torch.aten.relu",
            "args": [{"name": "self", "type": "AnyTorchTensorType"}],
            "returns": [{"name": "result", "type": "AnyTorchOptionalTensorType"}]
        }
    }
    """
    text = Path(td_file).read_text(encoding="utf-8")
    parsed: dict[str, dict[str, Any]] = {}

    for match in OP_BLOCK_RE.finditer(text):
        op_name = match.group("op_name")
        if _is_private_or_internal(op_name):
            continue
        body = match.group("body")
        parsed[op_name] = {
            "mlir_name": f"torch.{op_name}",
            "args": _extract_section(body, "arguments"),
            "returns": _extract_section(body, "results"),
        }

    save_json(DEFAULT_ALL_OPS_PATH, parsed)
    return parsed

