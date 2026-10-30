"""Run a frozen holdout on the existing A100 endpoint, with a shared host lease."""

# Endpoint functions are serialized as source and must carry their own imports.
# ruff: noqa: PLC0415

from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import time
import zlib
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/experiments/result-validity-audit-20261020"
ENDPOINT = "b162a840-38b4-4c1a-84cc-579fb62f4dfc"
REMOTE = "/tmp/lassi-accuracy-holdout-v1"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def remote(payload):
    """Self-contained endpoint handler; no imports from the host launcher."""
    import hashlib
    import io
    import json
    import os
    import shutil
    import subprocess
    import sys
    import tarfile
    import zlib
    from pathlib import Path

    root = Path(payload["root"])
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    operation = payload["operation"]
    python = payload.get("python_executable") or sys.executable
    if operation == "execution_logs":
        return {
            str(path.relative_to(root)): path.read_text(errors="replace")[-12000:]
            for path in (root / "control").rglob("launcher.log")
        }
    if operation == "inventory":
        runtime = subprocess.check_output(
            [
                python,
                "-c",
                "import json,sys,torch;print(json.dumps(dict("
                "device=torch.cuda.get_device_name(0),torch=torch.__version__,"
                "python=sys.executable)))",
            ],
            text=True,
            timeout=60,
        )
        return {
            **json.loads(runtime),
            "free_bytes": shutil.disk_usage(root).free,
            "assets": [p.name for p in assets.iterdir() if len(p.name) == 64],
            "processes": subprocess.check_output(
                ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
                text=True,
            ),
        }
    if operation == "stage":
        for item in payload["items"]:
            destination = assets / item["sha256"]
            if destination.exists():
                if hashlib.sha256(destination.read_bytes()).hexdigest() != item["sha256"]:
                    raise ValueError("Staged asset hash changed")
                continue
            part = assets / f"{item['sha256']}.{item['index']}.part"
            part.write_bytes(item["data"])
            if item["index"] == item["parts"] - 1:
                parts = [assets / f"{item['sha256']}.{i}.part" for i in range(item["parts"])]
                data = zlib.decompress(b"".join(p.read_bytes() for p in parts))
                if hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError("Transfer hash mismatch")
                destination.write_bytes(data)
                for chunk in parts:
                    chunk.unlink()
        return {"ok": True}
    if operation == "install":
        for relative, digest in payload["files"].items():
            source = assets / digest
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise ValueError("Frozen file hash mismatch")
            destination = root / "freeze" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                    raise ValueError("Remote freeze would be overwritten")
            else:
                os.link(source, destination)
        code = assets / payload["code_sha256"]
        if hashlib.sha256(code.read_bytes()).hexdigest() != payload["code_sha256"]:
            raise ValueError("Harness package hash mismatch")
        (root / "code").mkdir(exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(code.read_bytes()), mode="r:gz") as archive:
            archive.extractall(root / "code", filter="data")
        return {"ok": True}
    if operation == "jpeg_details":
        # Replay only existing cases and frozen sources; do not change decisions.
        code = """
import hashlib,json,sys
from pathlib import Path
import numpy as np
import torch
from lassi_x.candidate_runner import load_module
root=Path(sys.argv[1])
manifest=json.loads((root/'freeze/manifest.json').read_text())
policy=json.loads((root/'freeze/policy.json').read_text())
cases=['canonical_control']+[c['name'] for c in policy['cases']]
torch.set_num_threads(1)
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
records=[]
for target in manifest['targets']:
    if '/jpeg-dct/' not in target:continue
    relative=Path(target).parent
    source=root/'freeze'/relative/'repaired.py'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if digest!=manifest['files'][str(relative/'repaired.py')]:
        raise ValueError('Frozen source changed')
    module=load_module(source)
    for case in cases:
        folder=root/'results'/relative/case
        with np.load(folder/'inputs.npz',allow_pickle=False) as archive:
            image=np.array(archive['image'],copy=True)
        reference=np.load(folder/'reference.npy')
        model=module.make_model().to(device='cuda',dtype=torch.float16).eval()
        with torch.inference_mode():
            outputs=model(torch.from_numpy(image).to(device='cuda',dtype=torch.float16))
        row={'target':str(relative),'case':case,'source_sha256':digest,'components':{}}
        offset=0
        for name,part in zip(('image','mse','nonzero_count'),outputs,strict=True):
            value=part.detach().double().cpu().numpy().reshape(-1)
            expected=reference[offset:offset+value.size]
            offset+=value.size
            detail={'size':value.size,'finite':bool(np.isfinite(value).all()),
                    'nan_count':int(np.isnan(value).sum()),
                    'inf_count':int(np.isinf(value).sum())}
            if detail['finite']:
                detail['relative_l2']=float(np.linalg.norm(value-expected)/max(float(np.linalg.norm(expected)),1e-30))
            if value.size==1:
                actual=float(value[0])
                detail['value']=actual if np.isfinite(actual) else str(actual)
                detail['reference']=float(expected[0])
            row['components'][name]=detail
        records.append(row)
print(json.dumps(records,allow_nan=False))
"""
        env = dict(
            os.environ,
            PYTHONPATH=str(root / "code"),
            CUBLAS_WORKSPACE_CONFIG=":4096:8",
            PYTHONDONTWRITEBYTECODE="1",
        )
        result = subprocess.run(
            [python, "-c", code, str(root)],
            cwd=root / "code",
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
        )
        return {"records": json.loads(result.stdout), "stderr": result.stderr[-2000:]}
    target = payload["target"]
    relative = str(Path(target).parent)
    folder = root / "results" / relative
    control = root / "control" / relative
    control.mkdir(parents=True, exist_ok=True)
    launched, completion = control / "launched.json", control / "completion.json"
    if operation == "launch":
        if launched.exists():
            return json.loads(launched.read_text())
        command = [
            python,
            "-m",
            "lassi_x.holdout",
            "evaluate",
            "--manifest",
            str(root / "freeze/manifest.json"),
            "--target",
            str(root / "freeze" / target),
            "--results",
            str(folder),
            "--device",
            "cuda",
            "--timeout-s",
            str(payload["timeout_s"]),
        ]
        wrapper = (
            "import json,subprocess,sys\nfrom pathlib import Path\n"
            "data=json.loads(sys.argv[1])\n"
            "code=subprocess.call(data['command'])\n"
            "Path(data['completion']).write_text(json.dumps({'returncode':code}))\n"
        )
        env = dict(
            os.environ,
            PYTHONPATH=str(root / "code"),
            PYTHONDONTWRITEBYTECODE="1",
            CUBLAS_WORKSPACE_CONFIG=":4096:8",
            CUDA_VISIBLE_DEVICES=str(payload["physical_gpu"]),
            OMP_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
        )
        with (control / "launcher.log").open("ab") as log:
            process = subprocess.Popen(
                [
                    python,
                    "-c",
                    wrapper,
                    json.dumps({"command": command, "completion": str(completion)}),
                ],
                cwd=root / "code",
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        state = {"pid": process.pid, "target": target, "results": str(folder)}
        launched.write_text(json.dumps(state))
        return state
    if operation != "poll":
        raise ValueError("Unknown operation")
    cases = {}
    for path in folder.glob("*/result.json"):
        cases[path.parent.name] = json.loads(path.read_text())
    response = {
        "cases": cases,
        "remote_results": str(folder),
        "completion": json.loads(completion.read_text()) if completion.exists() else None,
    }
    if (folder / "summary.json").exists():
        response["summary"] = json.loads((folder / "summary.json").read_text())
    if (folder / "timeout.json").exists():
        response["timeout"] = json.loads((folder / "timeout.json").read_text())
    if (control / "launcher.log").exists():
        response["log_tail"] = (control / "launcher.log").read_text(errors="replace")[-8000:]
    return response


def run(args):
    global REMOTE
    REMOTE = f"/tmp/lassi-{args.output.name}"
    from globus_compute_sdk import Client, Executor
    from globus_compute_sdk.serialize import ComputeSerializer, DillCodeSource

    sys.path.insert(0, str(AUDIT))
    from gpu_coordination import A100Lease

    output, freeze = args.output.resolve(), args.freeze.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = (output / "launcher.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    manifest = json.loads((freeze / "manifest.json").read_text())
    records_path = output / "results.json"
    records = json.loads(records_path.read_text()) if records_path.exists() else {}

    def status(phase, **fields):
        write(
            output / "status.json",
            {
                "status": phase,
                "pid": os.getpid(),
                "updated_at": datetime.now(UTC).isoformat(),
                "completed_targets": len(records),
                "total_targets": len(manifest["targets"]),
                "model_calls": 0,
                "freeze": str(freeze),
                **fields,
            },
        )

    if not args.inspect_jpeg:
        status("connecting")
    executor = Executor(
        endpoint_id=ENDPOINT,
        client=Client(),
        serializer=ComputeSerializer(strategy_code=DillCodeSource()),
    )

    def call(operation, **fields):
        future = executor.submit(
            remote,
            {
                "operation": operation,
                "root": REMOTE,
                "python_executable": args.remote_python,
                **fields,
            },
        )
        write(
            output / ("jpeg-active-task.json" if args.inspect_jpeg else "active-task.json"),
            {
                "operation": operation,
                "task_id": str(future.task_id),
                "at": datetime.now(UTC).isoformat(),
            },
        )
        return future.result(timeout=180)

    if args.inspect_jpeg:
        with A100Lease():
            details = call("jpeg_details")
        write(output / "jpeg-output-components.json", details)
        print("Saved JPEG component diagnostics", flush=True)
        sys.stdout.flush()
        os._exit(0)

    with A100Lease():
        inventory = call("inventory")
    write(output / "endpoint.json", inventory)
    if inventory["free_bytes"] < 20 * 1024**3:
        raise RuntimeError("Less than 20 GiB free for the full holdout evidence")
    files = {
        str(p.relative_to(freeze)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in freeze.rglob("*")
        if p.is_file()
    }
    assets = {digest: (freeze / name).read_bytes() for name, digest in files.items()}
    code_buffer = io.BytesIO()
    with tarfile.open(fileobj=code_buffer, mode="w:gz") as archive:
        for path in sorted((ROOT / "lassi_x").rglob("*.py")):
            archive.add(path, arcname=str(path.relative_to(ROOT)))
    code = code_buffer.getvalue()
    code_sha = hashlib.sha256(code).hexdigest()
    assets[code_sha] = code
    write(
        output / "transport.json",
        {
            "endpoint": ENDPOINT,
            "remote": REMOTE,
            "package_sha256": code_sha,
            "files": files,
            "python_executable": args.remote_python,
        },
    )
    cached = set(inventory["assets"])
    status("staging", assets=len(assets))
    staged_batch, staged_bytes = [], 0

    def flush():
        if staged_batch:
            call("stage", items=staged_batch)
            print("STAGED_BATCH", len(staged_batch), "chunks", flush=True)
            staged_batch.clear()

    for digest, data in assets.items():
        if digest in cached:
            continue
        compressed = zlib.compress(data, 6)
        chunks = [compressed[i : i + 1_000_000] for i in range(0, len(compressed), 1_000_000)]
        for part, chunk in enumerate(chunks):
            if staged_bytes + len(chunk) > 2_000_000 or len(staged_batch) >= 16:
                flush()
                staged_bytes = 0
            staged_batch.append(
                {"sha256": digest, "data": chunk, "index": part, "parts": len(chunks)}
            )
            staged_bytes += len(chunk)
    flush()
    call("install", files=files, code_sha256=code_sha)
    for target in manifest["targets"]:
        if target in records:
            continue
        status("waiting_for_a100", current=target)
        with A100Lease() as lease:
            launched = call(
                "launch", target=target, timeout_s=args.timeout_s, physical_gpu=args.physical_gpu
            )
            write(output / "current-remote.json", launched)
            print("RUNNING", target, "remote PID", launched["pid"], flush=True)
            while True:
                try:
                    progress = call("poll", target=target)
                except Exception as exc:
                    # Retain GPU ownership while completion is uncertain.
                    status("poll_connection_error", current=target, error=str(exc))
                    time.sleep(15)
                    continue
                local = output / Path(target).parent
                write(local / "progress.json", progress)
                status(
                    "running",
                    current=target,
                    completed_cases=len(progress["cases"]),
                    shared_gpu_queue_wait_s=lease.wait_s,
                    remote_pid=launched["pid"],
                    remote_results=progress["remote_results"],
                )
                if progress["completion"] is not None:
                    records[target] = progress
                    write(records_path, records)
                    if "summary" in progress:
                        write(local / "summary.json", progress["summary"])
                    print(
                        "FINISHED",
                        target,
                        progress.get("summary", {}).get("passed"),
                        progress["completion"],
                        flush=True,
                    )
                    break
                time.sleep(10)
    status(
        "completed",
        passed_targets=sum(v.get("summary", {}).get("passed", False) for v in records.values()),
    )
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout-s", type=float, default=86400)
    parser.add_argument("--physical-gpu", type=int, default=0)
    parser.add_argument("--remote-python", default=None)
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--restart-staging", action="store_true")
    parser.add_argument("--inspect-jpeg", action="store_true")
    args = parser.parse_args()
    if args.detach:
        args.output.mkdir(parents=True, exist_ok=True)
        if args.restart_staging:
            import signal

            state = json.loads((args.output / "status.json").read_text())
            if state["status"] != "staging":
                raise RuntimeError("Restart is restricted to staging, before target launch")
            os.kill(state["pid"], signal.SIGTERM)
            with (args.output / "launcher.lock").open("a") as prior:
                fcntl.flock(prior, fcntl.LOCK_EX)
                fcntl.flock(prior, fcntl.LOCK_UN)
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--freeze",
            str(args.freeze.resolve()),
            "--output",
            str(args.output.resolve()),
            "--timeout-s",
            str(args.timeout_s),
            "--physical-gpu",
            str(args.physical_gpu),
        ]
        if args.remote_python:
            command.extend(["--remote-python", args.remote_python])
        with (args.output / "launcher.log").open("ab") as log:
            child = subprocess.Popen(
                command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
            )
        print("Started holdout launcher PID", child.pid, flush=True)
        return
    try:
        run(args)
    except Exception as exc:
        write(
            args.output / ("jpeg-failure.json" if args.inspect_jpeg else "failure.json"),
            {"error": f"{type(exc).__name__}: {exc}", "at": datetime.now(UTC).isoformat()},
        )
        raise


if __name__ == "__main__":
    main()
