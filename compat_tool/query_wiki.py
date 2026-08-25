"""Query helper for the generated compatibility wiki."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from compat_tool.utils import DEFAULT_DB_PATH, WIKI_DIR, load_json


def load_db(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, dict[str, Any]]:
    """Load the compatibility database from disk."""
    return load_json(db_path, default={})


def query_op(op_name: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    """Return the database record for one op, if it exists."""
    return load_db(db_path).get(op_name)


def search_ops(
    pattern: str,
    supported: bool | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> list[str]:
    """Return ops whose names contain `pattern`, optionally filtered by support."""
    database = load_db(db_path)
    matches: list[str] = []
    needle = pattern.lower()

    for op_name, info in sorted(database.items()):
        if needle not in op_name.lower():
            continue
        if supported is not None and bool(info.get("supported")) is not supported:
            continue
        matches.append(op_name)

    return matches


def get_markdown_path(op_name: str, wiki_dir: str | Path = WIKI_DIR) -> Path:
    """Return the markdown file path for an op."""
    return Path(wiki_dir) / f"{op_name}.md"


def read_markdown(op_name: str, wiki_dir: str | Path = WIKI_DIR) -> str | None:
    """Read the generated markdown page for an op, if present."""
    path = get_markdown_path(op_name, wiki_dir)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(description="Query the generated Torch-MLIR/TOSA wiki")
    subparsers = parser.add_subparsers(dest="command", required=True)

    op_parser = subparsers.add_parser("op", help="Show one op entry")
    op_parser.add_argument("op_name")
    op_parser.add_argument("--markdown", action="store_true", help="Print the markdown page instead of the DB record")

    search_parser = subparsers.add_parser("search", help="Search ops by substring")
    search_parser.add_argument("pattern")
    group = search_parser.add_mutually_exclusive_group()
    group.add_argument("--supported", action="store_true")
    group.add_argument("--unsupported", action="store_true")

    return parser


def main() -> None:
    """CLI entrypoint for wiki queries."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "op":
        if args.markdown:
            markdown = read_markdown(args.op_name)
            if markdown is None:
                raise SystemExit(f"No markdown page found for {args.op_name}")
            print(markdown, end="")
            return

        info = query_op(args.op_name)
        if info is None:
            raise SystemExit(f"Unknown op: {args.op_name}")

        status = "supported" if info.get("supported") else "unsupported"
        print(f"op: {args.op_name}")
        print(f"status: {status}")
        print(f"error: {info.get('error') or 'None'}")
        print(f"wiki: {get_markdown_path(args.op_name)}")
        return

    support_filter = True if args.supported else False if args.unsupported else None
    for op_name in search_ops(args.pattern, supported=support_filter):
        print(op_name)


if __name__ == "__main__":
    main()
