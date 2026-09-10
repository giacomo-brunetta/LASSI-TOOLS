"""Command line interface for the compatibility database."""

# Subcommand imports are intentionally lazy: query/list operations should not
# require target-vendor compiler packages.
# ruff: noqa: PLC0415

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lassi_x.compat.io import DEFAULT_PRUNING_PATH, PACKAGE_ROOT


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lassi-x-compat", description="Generate and query target compiler compatibility"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Build and validate a canonical probe manifest")
    prepare.add_argument("--torch-mlir-root", type=Path, required=True)
    prepare.add_argument("--revision", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--pruning", type=Path, default=DEFAULT_PRUNING_PATH)
    prepare.add_argument("--precision", action="append", choices=["fp64", "fp32", "fp16", "bf16"])
    prepare.add_argument("--op", action="append", dest="ops")

    probe = subparsers.add_parser("probe", help="Run a manifest through one local target checker")
    probe.add_argument("--manifest", type=Path, required=True)
    probe.add_argument("--target", type=Path, required=True)
    probe.add_argument("--run-dir", type=Path, required=True)
    probe.add_argument("--resume", action="store_true")
    probe.add_argument("--op", action="append", dest="ops")
    probe.add_argument("--limit", type=int)

    publish = subparsers.add_parser("publish", help="Write a target snapshot and independent wiki")
    publish.add_argument("--manifest", type=Path, required=True)
    publish.add_argument("--results", type=Path, required=True)
    publish.add_argument("--output-root", type=Path, default=PACKAGE_ROOT)

    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "prepare":
        from lassi_x.compat.inventory import prepare_from_checkout

        manifest = prepare_from_checkout(
            args.torch_mlir_root,
            args.revision,
            args.output,
            pruning_path=args.pruning,
            precisions=args.precision,
            selected_ops=set(args.ops) if args.ops else None,
        )
        print(json.dumps({"output": str(args.output), "summary": manifest["summary"]}, indent=2))
        return 1 if manifest["summary"]["needs_fixture"] else 0

    if args.command == "probe":
        from lassi_x.compat.probe import run_probe

        result = run_probe(
            args.manifest,
            args.target,
            args.run_dir,
            resume=args.resume,
            selected_ops=set(args.ops) if args.ops else None,
            limit=args.limit,
        )
        print(
            json.dumps(
                {"results": str(args.run_dir / "results.json"), "summary": result["summary"]},
                indent=2,
            )
        )
        return 0 if result["complete"] else 1

    if args.command == "publish":
        from lassi_x.compat.publish import publish_snapshot

        snapshot, snapshot_path, wiki_path = publish_snapshot(
            args.manifest, args.results, args.output_root
        )
        print(
            json.dumps(
                {
                    "snapshot": str(snapshot_path),
                    "wiki": str(wiki_path),
                    "summary": snapshot["summary"],
                },
                indent=2,
            )
        )
        return 0 if snapshot["complete"] else 1

    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
