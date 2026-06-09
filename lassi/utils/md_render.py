"""Render LASSI tool outputs (dict / list / JSON string / plain text) as Markdown.

Used by the CLI wrappers (`cli/lassi-*`) so the LLM-facing output shape
stays consistent across tools. The on-disk JSON artifact files that
downstream LASSI tools consume are NOT touched by this module — only the
human/LLM-facing representation is rewritten.
"""

from __future__ import annotations

import json
import math
from typing import Any


def _is_scalar(v: Any) -> bool:
    return v is None or isinstance(v, (str, int, float, bool))


def _fmt_scalar(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if not math.isfinite(v):
            return str(v)
        if v == 0:
            return "0"
        if abs(v) < 1e-3 or abs(v) >= 1e6:
            return f"{v:.3e}"
        return f"{v:.4g}"
    return str(v)


def _fmt_cell(v: Any) -> str:
    """Scalar formatter safe to drop into a markdown table cell."""
    return _fmt_scalar(v).replace("|", "\\|").replace("\n", " ↵ ")


def _fmt_inline_list(items: list) -> str:
    return ", ".join(_fmt_scalar(x) for x in items)


def _render(data: Any, lines: list[str], level: int) -> None:
    if isinstance(data, dict):
        scalars: list[tuple[str, Any]] = []
        nested: list[tuple[str, Any]] = []
        for k, v in data.items():
            if isinstance(v, dict) and v:
                nested.append((k, v))
            elif isinstance(v, list) and v and not all(_is_scalar(x) for x in v):
                nested.append((k, v))
            else:
                scalars.append((k, v))

        for k, v in scalars:
            if isinstance(v, list):
                if not v:
                    lines.append(f"- **{k}**: —")
                elif len(v) <= 8:
                    lines.append(f"- **{k}**: {_fmt_inline_list(v)}")
                else:
                    lines.append(f"- **{k}**:")
                    for item in v:
                        lines.append(f"  - {_fmt_scalar(item)}")
            elif isinstance(v, str) and "\n" in v:
                lines.append(f"- **{k}**:")
                lines.append("  ```")
                for ln in v.splitlines():
                    lines.append(f"  {ln}")
                lines.append("  ```")
            else:
                lines.append(f"- **{k}**: {_fmt_scalar(v)}")

        for k, v in nested:
            lines.append("")
            lines.append(f"{'#' * min(level, 6)} {k}")
            lines.append("")
            _render(v, lines, level + 1)

    elif isinstance(data, list):
        if data and all(isinstance(item, dict) for item in data):
            cols: list[str] = []
            for d in data:
                for k in d.keys():
                    if k not in cols:
                        cols.append(k)
            lines.append("| " + " | ".join(cols) + " |")
            lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
            for d in data:
                lines.append("| " + " | ".join(_fmt_cell(d.get(c)) for c in cols) + " |")
        else:
            for item in data:
                lines.append(f"- {_fmt_scalar(item)}")
    else:
        lines.append(_fmt_scalar(data))


def to_md(data: Any, *, title: str | None = None) -> str:
    """Render a Python value as Markdown.

    Conventions:
      - dict: scalar fields first as bullets, then nested sections as ##
        headings (one deeper per nesting level, capped at h6)
      - list of dicts: rendered as a Markdown table (union of keys = columns)
      - list of scalars ≤ 8 items: inline comma-joined; > 8: bullets
      - long multi-line strings: wrapped in a fenced code block
    """
    lines: list[str] = []
    if title:
        lines.append(f"# {title}")
        lines.append("")
    _render(data, lines, level=2)
    return "\n".join(lines).rstrip() + "\n"


def render_for_output(result: Any, *, title: str | None = None) -> str:
    """Take an impl result (dict, list, JSON string, plain text, or None) and
    produce a Markdown string suitable for printing to stdout from a
    ``cli/lassi-*`` script.

    - None → empty string.
    - dict / list → `to_md(result, title=title)`.
    - str that JSON-parses to dict/list → `to_md(parsed, title=title)`.
    - other str → wrapped under `# {title}` (if title) preserving text as-is.
    - any other type → its `_fmt_scalar` form.
    """
    if result is None:
        return ""

    if isinstance(result, (dict, list)):
        return to_md(result, title=title)

    if isinstance(result, str):
        stripped = result.strip()
        if stripped and stripped[0] in "[{":
            try:
                data = json.loads(stripped)
                return to_md(data, title=title)
            except json.JSONDecodeError:
                pass
        if title:
            return f"# {title}\n\n{result.rstrip()}\n"
        return result.rstrip() + "\n"

    return _fmt_scalar(result) + "\n"
