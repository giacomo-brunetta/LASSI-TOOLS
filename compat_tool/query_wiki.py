"""Query helper for the generated compatibility wiki."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, cast

from compat_tool.io import DEFAULT_DB_PATH, SNAPSHOT_DIR, WIKI_DIR, load_json

LEGACY_TARGET = "legacy-torch-mlir-tosa"


def list_targets(snapshot_dir: str | Path = SNAPSHOT_DIR) -> list[dict[str, Any]]:
    """List published targets plus the restored legacy corpus."""
    targets = [
        {
            "target_id": LEGACY_TARGET,
            "family": "torch-mlir-tosa",
            "legacy": True,
            "complete": False,
        }
    ]
    root = Path(snapshot_dir)
    if root.is_dir():
        for snapshot_path in sorted(root.glob("*/snapshot.json")):
            snapshot = cast("dict[str, Any]", load_json(snapshot_path, default={}))
            target = dict(snapshot.get("target") or {})
            if target.get("target_id"):
                target.update(
                    {
                        "legacy": False,
                        "complete": bool(snapshot.get("complete")),
                        "snapshot_hash": snapshot.get("snapshot_hash"),
                    }
                )
                targets.append(target)
    return targets


def load_snapshot(target: str, snapshot_dir: str | Path = SNAPSHOT_DIR) -> dict[str, Any]:
    if target == LEGACY_TARGET:
        return {
            "target": {"target_id": LEGACY_TARGET, "family": "torch-mlir-tosa"},
            "legacy": True,
            "operators": load_json(DEFAULT_DB_PATH, default={}),
        }
    path = Path(snapshot_dir) / target / "snapshot.json"
    if not path.is_file():
        raise FileNotFoundError(f"No published compatibility snapshot for target {target}")
    return cast("dict[str, Any]", load_json(path))


def query_target_op(
    target: str,
    op_name: str,
    precision: str | None = None,
    snapshot_dir: str | Path = SNAPSHOT_DIR,
) -> dict[str, Any] | None:
    snapshot = load_snapshot(target, snapshot_dir)
    entry = snapshot["operators"].get(op_name)
    if entry is None or snapshot.get("legacy") or precision is None:
        return cast("dict[str, Any] | None", entry)
    cases = entry.get("cases") or {}
    return {**entry, "cases": {precision: cases.get(precision, {})}}


def search_target_ops(
    target: str,
    pattern: str,
    *,
    precision: str | None = None,
    supported: bool | None = None,
    snapshot_dir: str | Path = SNAPSHOT_DIR,
) -> list[str]:
    snapshot = load_snapshot(target, snapshot_dir)
    matches: list[str] = []
    for op_name, entry in sorted(snapshot["operators"].items()):
        if pattern.lower() not in op_name.lower():
            continue
        if supported is not None:
            if snapshot.get("legacy"):
                is_supported = bool(entry.get("supported"))
            else:
                precisions = [precision] if precision else list((entry.get("cases") or {}).keys())
                statuses = [
                    case["result"].get("status")
                    for item in precisions
                    for case in (entry.get("cases") or {}).get(item, {}).values()
                ]
                is_supported = bool(statuses) and all(status == "compiled" for status in statuses)
            if is_supported is not supported:
                continue
        matches.append(op_name)
    return matches


def load_db(db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, dict[str, Any]]:
    """Load the compatibility database from disk."""
    return cast("dict[str, dict[str, Any]]", load_json(db_path, default={}))


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
    parser = argparse.ArgumentParser(
        description="Query target-specific compiler compatibility wikis"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("targets", help="List published compatibility targets")

    op_parser = subparsers.add_parser("op", help="Show one op entry")
    op_parser.add_argument("op_name")
    op_parser.add_argument("--target", required=True)
    op_parser.add_argument("--precision")
    op_parser.add_argument(
        "--markdown", action="store_true", help="Print the markdown page instead of the DB record"
    )

    search_parser = subparsers.add_parser("search", help="Search ops by substring")
    search_parser.add_argument("pattern")
    search_parser.add_argument("--target", required=True)
    search_parser.add_argument("--precision")
    group = search_parser.add_mutually_exclusive_group()
    group.add_argument("--supported", action="store_true")
    group.add_argument("--unsupported", action="store_true")

    return parser


def main() -> None:
    """CLI entrypoint for wiki queries."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "targets":
        for target in list_targets():
            suffix = (
                " legacy" if target["legacy"] else " complete" if target["complete"] else " partial"
            )
            print(f"{target['target_id']} ({target['family']};{suffix.strip()})")
        return

    if args.command == "op":
        if args.target == LEGACY_TARGET:
            print("warning: querying a stale legacy Torch-MLIR/TOSA snapshot", file=sys.stderr)
        if args.markdown:
            selected_wiki = WIKI_DIR if args.target == LEGACY_TARGET else WIKI_DIR / args.target
            markdown = read_markdown(args.op_name, selected_wiki)
            if markdown is None:
                raise SystemExit(f"No markdown page found for {args.op_name}")
            print(markdown, end="")
            return

        info = query_target_op(args.target, args.op_name, args.precision)
        if info is None:
            raise SystemExit(f"Unknown op: {args.op_name}")

        print(f"op: {args.op_name}")
        print(f"target: {args.target}")
        if args.target == LEGACY_TARGET:
            print(f"status: {'supported' if info.get('supported') else 'unsupported'}")
            print(f"error: {info.get('error') or 'None'}")
        else:
            print(json.dumps(info, indent=2, sort_keys=True))
        selected_wiki = WIKI_DIR if args.target == LEGACY_TARGET else WIKI_DIR / args.target
        print(f"wiki: {get_markdown_path(args.op_name, selected_wiki)}")
        return

    support_filter = True if args.supported else False if args.unsupported else None
    for op_name in search_target_ops(
        args.target, args.pattern, precision=args.precision, supported=support_filter
    ):
        print(op_name)


if __name__ == "__main__":
    main()
