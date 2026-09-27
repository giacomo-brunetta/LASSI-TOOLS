"""Resume unsolved CPU-suite kernels sequentially from their safest checkpoint."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    output = args.output.resolve()
    root = Path(__file__).resolve().parents[2]

    if args.detach:
        if output.exists():
            raise ValueError(f"Refusing to reuse launcher output: {output}")
        output.mkdir(parents=True)
        with (output / "launcher.log").open("x") as log:
            process = subprocess.Popen(
                [sys.executable, "-u", str(Path(__file__).resolve()), str(manifest_path),
                 "--output", str(output)],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Started resume launcher PID {process.pid}; log: {output / 'launcher.log'}")
        return 0

    output.mkdir(parents=True, exist_ok=True)
    status_path = output / "status.json"
    if status_path.exists():
        raise ValueError(f"Refusing to overwrite launcher status: {status_path}")
    manifest = json.loads(manifest_path.read_text())
    executable = root / ".venv/bin/lassi-x"
    state = {"pid": os.getpid(), "started_at": datetime.now(UTC).isoformat(),
             "status": "running", "kernels": []}

    def save() -> None:
        status_path.write_text(json.dumps(state, indent=2) + "\n")

    save()
    for spec in manifest["entries"]:
        name = spec["name"]
        run_jsons = sorted((manifest_path.parent / "runs" / name).glob("*/run.json"))
        records = [(path, json.loads(path.read_text())) for path in run_jsons]
        if any(record.get("status") == "cpu_verified" and
               record.get("accuracy", {}).get("kernel_solved") for _, record in records):
            continue
        latest_path, latest = records[-1]
        run_dir = latest_path.parent
        checkpoint_path = run_dir / "checkpoint.json"
        checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {}
        # A planner failure has no candidate journals and can be resumed exactly. Candidate
        # crashes are journaled as terminal, so those require a clean candidate attempt.
        exact_resume = checkpoint.get("completed_stages") == ["build_oracle"]
        config = manifest_path.parent / spec["config"]
        command = [str(executable), "run", str(config)]
        if exact_resume:
            command.extend(["--resume", str(run_dir)])
        command.extend(["--until", "cpu-verified"])
        entry = {"kernel": name, "mode": "resume" if exact_resume else "fresh",
                 "source_run": str(run_dir), "status": "running"}
        state["kernels"].append(entry)
        save()
        print(subprocess.list2cmdline(command), flush=True)
        result = subprocess.run(command, cwd=root, check=False)
        entry.update(status="finished", returncode=result.returncode)
        save()
        if result.returncode:
            new_records = sorted((manifest_path.parent / "runs" / name).glob("*/run.json"))
            outcome_path = latest_path if exact_resume else new_records[-1]
            outcome = json.loads(outcome_path.read_text())
            if "connection error" in json.dumps(outcome).lower():
                state["status"] = "endpoint_unreachable"
                save()
                return 3
    state["status"] = "finished"
    save()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
