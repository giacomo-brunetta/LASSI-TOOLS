"""Query helper for the generated compatibility wiki."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

import yaml

from lassi_x.compat.io import TARGET_DIR, load_json


def list_targets(target_dir: str | Path = TARGET_DIR) -> list[dict[str, Any]]:
    """List configured compiler and accelerator targets."""
    targets: list[dict[str, Any]] = []
    root = Path(target_dir)
    if root.is_dir():
        for config_path in sorted(root.glob("*/target.yaml")):
            config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            snapshot_path = config_path.parent / "snapshot.json"
            snapshot = cast("dict[str, Any]", load_json(snapshot_path, default={}))
            target = dict(snapshot.get("target") or config)
            if target.get("target_id"):
                target.update(
                    {
                        "published": snapshot_path.is_file(),
                        "complete": bool(snapshot.get("complete")),
                        "result_format": snapshot.get("result_format", "target-cases"),
                        "snapshot_hash": snapshot.get("snapshot_hash"),
                    }
                )
                targets.append(target)
    return targets


def load_snapshot(target: str, target_dir: str | Path = TARGET_DIR) -> dict[str, Any]:
    path = Path(target_dir) / target / "snapshot.json"
    if not path.is_file():
        raise FileNotFoundError(f"No published compatibility snapshot for target {target}")
    return cast("dict[str, Any]", load_json(path))


def query_target_op(
    target: str,
    op_name: str,
    precision: str | None = None,
    target_dir: str | Path = TARGET_DIR,
) -> dict[str, Any] | None:
    snapshot = load_snapshot(target, target_dir)
    entry = snapshot["operators"].get(op_name)
    if entry is None or snapshot.get("result_format") == "flat-support" or precision is None:
        return cast("dict[str, Any] | None", entry)
    cases = entry.get("cases") or {}
    return {**entry, "cases": {precision: cases.get(precision, {})}}


def search_target_ops(
    target: str,
    pattern: str,
    *,
    precision: str | None = None,
    supported: bool | None = None,
    target_dir: str | Path = TARGET_DIR,
) -> list[str]:
    snapshot = load_snapshot(target, target_dir)
    matches: list[str] = []
    for op_name, entry in sorted(snapshot["operators"].items()):
        if pattern.lower() not in op_name.lower():
            continue
        if supported is not None:
            if snapshot.get("result_format") == "flat-support":
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


def get_markdown_path(op_name: str, wiki_dir: str | Path) -> Path:
    """Return the markdown file path for an op."""
    return Path(wiki_dir) / f"{op_name}.md"


def read_markdown(op_name: str, wiki_dir: str | Path) -> str | None:
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
            if not target["published"]:
                status = "configured; no snapshot"
            elif target["result_format"] == "flat-support":
                status = "preserved results"
            else:
                status = "complete" if target["complete"] else "partial"
            print(f"{target['target_id']} ({target['family']}; {status})")
        return

    if args.command == "op":
        if args.markdown:
            selected_wiki = TARGET_DIR / args.target / "wiki"
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
        snapshot = load_snapshot(args.target)
        if snapshot.get("result_format") == "flat-support":
            print(f"status: {'supported' if info.get('supported') else 'unsupported'}")
            print(f"error: {info.get('error') or 'None'}")
        else:
            print(json.dumps(info, indent=2, sort_keys=True))
        selected_wiki = TARGET_DIR / args.target / "wiki"
        print(f"wiki: {get_markdown_path(args.op_name, selected_wiki)}")
        return

    support_filter = True if args.supported else False if args.unsupported else None
    for op_name in search_target_ops(
        args.target, args.pattern, precision=args.precision, supported=support_filter
    ):
        print(op_name)


if __name__ == "__main__":
    main()
