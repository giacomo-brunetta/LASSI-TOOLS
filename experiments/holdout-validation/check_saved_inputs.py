"""Check frozen candidate builders against original C inputs; no forward/model calls.

Run with the repository Torch environment. This never changes the campaign.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from lassi_x.c_inputs import build_input_contract
from lassi_x.candidate_runner import run_module
from lassi_x.config import RunConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--one-per-kernel", action="store_true")
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    import torch  # noqa: PLC0415

    torch.set_num_threads(1)
    root = Path(__file__).resolve().parents[2]
    snapshot = json.loads(args.snapshot.read_text())
    selected = [r for r in snapshot["sources"] if r["status"] == "ok"]
    if args.one_per_kernel:
        selected = list({r["kernel"]: r for r in reversed(selected)}.values())
    contracts = {}
    results = []
    args.output.mkdir(parents=True, exist_ok=True)
    for row in selected:
        module = root / row["path"]
        if hashlib.sha256(module.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"candidate changed since snapshot: {module}")
        config = RunConfig.load(root / Path(row["run"]).parent / "resolved-config.yaml")
        key = (row["model"], row["kernel"])
        if key not in contracts:
            contracts[key] = asyncio.run(
                build_input_contract(
                    config, args.output / "c-inputs" / row["model"] / row["kernel"]
                )
            )
        label = f"{row['model']}/{row['kernel']}/{row['candidate']}"
        report_path = (
            args.output / "candidates" / row["model"] / row["kernel"] / f"{row['candidate']}.json"
        )
        record = {k: row[k] for k in ("model", "kernel", "candidate", "path", "sha256")}
        # These positional bindings are trusted, reviewed legacy interfaces,
        # not values or declarations taken from candidate metadata.
        bindings = {}
        if row["kernel"] == "polybench-3mm":
            bindings = {f"#{i}": k for i, k in enumerate(("A", "B", "C", "D"))}
        elif row["kernel"] == "poisson-cg":
            bindings = {f"#{i}": k for i, k in enumerate(("x", "r", "p", "ap", "rr"))}
        elif row["kernel"] == "low-rank-compression":
            bindings = {f"#{i}": k for i, k in enumerate(("image", "residual", "approximation"))}
        try:
            run_module(
                module,
                device="cpu",
                precision="fp64",
                dataset=config.kernel.validation_dataset,
                input_contract=contracts[key],
                input_report=report_path,
                input_snapshot=report_path.with_suffix(".npz"),
                input_bindings=bindings,
                inputs_only=True,
            )
            record["ok"] = True
        except Exception as exc:  # noqa: BLE001
            record.update(ok=False, error=f"{type(exc).__name__}: {exc}")
        results.append(record)
        print(f"{label}: {'PASS' if record['ok'] else 'FAIL'}", flush=True)
        (args.output / "results.json").write_text(
            json.dumps(
                {
                    "scope": (
                        "CPU FP64 supplied-input parity; forward not executed; no model API calls"
                    ),
                    "snapshot_sha256": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
                    "counts": dict(Counter("pass" if r["ok"] else "fail" for r in results)),
                    "candidates": results,
                },
                indent=2,
            )
            + "\n"
        )
    print(
        json.dumps(
            {
                "applications": len({r["kernel"] for r in results}),
                "counts": dict(Counter("pass" if r["ok"] else "fail" for r in results)),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
