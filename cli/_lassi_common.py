"""Shared helpers for the lassi-* CLI wrappers.

Each cli/lassi-<tool> script does:

    from _lassi_common import setup_path, run_async, add_json_arg, get_json_arg
    setup_path()

then builds an argparse parser, resolves JSON-shaped args with get_json_arg,
and calls the matching lassi.* impl coroutine inside run_async(...). The
result — whether a plain string or a JSON document — is rendered as Markdown
for stdout. Pass `title="..."` to run_async so the output has a top heading.

Pipeline JSON artifacts (the files downstream LASSI tools read) are written
by the impls themselves and are not affected by the stdout rendering.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Awaitable, Callable


# ---------------------------------------------------------------------------
# argparse / path helpers
# ---------------------------------------------------------------------------


def setup_path() -> Path:
    """Put the repo root (parent of cli/) on sys.path so `lassi.*` imports work."""
    cli_dir = Path(__file__).resolve().parent
    repo_root = cli_dir.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def add_json_arg(
    parser: argparse.ArgumentParser,
    name: str,
    help: str,
    required: bool = False,
) -> None:
    """Add --<name> (inline JSON) and --<name>-file (path to JSON file)."""
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument(
        f"--{name}",
        dest=name.replace("-", "_"),
        metavar="JSON",
        help=help + " (inline JSON string)",
    )
    group.add_argument(
        f"--{name}-file",
        dest=name.replace("-", "_") + "_file",
        metavar="PATH",
        help=help + " (path to JSON file)",
    )


def get_json_arg(args: argparse.Namespace, name: str, default: Any = None) -> Any:
    attr = name.replace("-", "_")
    inline = getattr(args, attr, None)
    path = getattr(args, attr + "_file", None)
    if inline is not None:
        try:
            return json.loads(inline)
        except json.JSONDecodeError as e:
            raise SystemExit(f"--{name}: invalid JSON ({e})")
    if path is not None:
        try:
            return json.loads(Path(path).read_text())
        except (OSError, json.JSONDecodeError) as e:
            raise SystemExit(f"--{name}-file: {e}")
    return default


def split_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return parts or None


# ---------------------------------------------------------------------------
# Markdown rendering (lassi.utils.md_render)
# ---------------------------------------------------------------------------


def _emit(result: Any, *, title: str | None) -> None:
    setup_path()  # ensure lassi/ is importable when called before main()
    from lassi.utils.md_render import render_for_output
    text = render_for_output(result, title=title)
    if text:
        sys.stdout.write(text)


def run_async(
    value: Awaitable[Any] | Callable[[], Awaitable[Any]] | Any,
    *,
    title: str | None = None,
) -> int:
    """Run an awaitable (or sync value), render the result as Markdown, return
    an exit code. On error, emit a small Markdown error block to stderr with
    rc=1.
    """
    try:
        if callable(value) and not inspect.iscoroutine(value):
            value = value()
        if inspect.iscoroutine(value) or inspect.isawaitable(value):
            result = asyncio.run(value)
        else:
            result = value
        _emit(result, title=title)
        return 0
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write(f"# Error\n\n- **type**: {type(e).__name__}\n- **message**: {e}\n")
        if "--debug" in sys.argv:
            traceback.print_exc(file=sys.stderr)
        return 1
