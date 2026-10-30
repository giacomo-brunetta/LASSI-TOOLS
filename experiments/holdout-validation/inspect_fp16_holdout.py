"""Diagnose rejected outputs without changing qualification results."""

# Endpoint functions are serialized independently of module globals.
# ruff: noqa: PLC0415

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lassi_x.holdout import read, write

ROOT = Path(__file__).resolve().parents[2]


def inspect(payload):
    import hashlib
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    root = Path(payload["root"])
    role = payload.get("role", "repaired")
    if role not in {"baseline", "repaired"}:
        raise ValueError(f"Unknown source role: {role}")
    program = r"""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import torch
from lassi_x.holdout import input_values
from lassi_x.candidate_runner import load_module
root=Path(sys.argv[1]); requests=json.loads(sys.argv[2]); role=sys.argv[3]
manifest=json.loads((root/'freeze/manifest.json').read_text())
torch.set_num_threads(1)
torch.backends.cuda.matmul.allow_tf32=False
torch.backends.cudnn.allow_tf32=False
torch.use_deterministic_algorithms(True,warn_only=True)
records=[]
for target,cases in requests.items():
    assert target in manifest['targets']
    rel=Path(target).parent; folder=root/'freeze'/rel
    spec=json.loads((folder/'target.json').read_text())
    schema=json.loads((folder/'schema.json').read_text())
    source=folder/(role+'.py')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest==manifest['files'][str(rel/(role+'.py'))]
    module=load_module(source)
    for case in cases:
        archive=root/'results'/rel/case/'inputs.npz'
        with np.load(archive,allow_pickle=False) as z:
            arrays={n:z[n].copy() for n in z.files}
        values=input_values(arrays,schema,spec)
        model=module.make_model().to(device='cuda',dtype=torch.float16).eval()
        outputs=[]
        for repeat in range(2):
            supplied=[]
            for s,v in zip(schema,values,strict=True):
                if s['kind']=='tensor':
                    dtype=getattr(torch,s['integer_dtype']) if s['integer_dtype'] else torch.float16
                    x=torch.empty_strided(s['shape'],s['stride'],dtype=dtype,device='cuda')
                    x.copy_(torch.from_numpy(v).to(device='cuda',dtype=dtype))
                    supplied.append(x)
                else:
                    supplied.append({'int':int,'float':float,'bool':bool}[s['kind']](v.item()))
            with torch.inference_mode():
                output=model(*supplied)
            parts=output if isinstance(output,(tuple,list)) else (output,)
            pieces=[p.detach().double().cpu().numpy().reshape(-1) for p in parts]
            outputs.append(np.concatenate(pieces))
        reference=np.load(root/'results'/rel/case/'reference.npy',allow_pickle=False)
        records.append({'target':target,'case':case,'role':role,'source_sha256':digest,
            'reference_size':reference.size,
            'input_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'bitwise_equal':bool(np.array_equal(*outputs)),
            'equal_including_nan':bool(np.array_equal(*outputs,equal_nan=True)),
            'outputs':[{'size':o.size,'finite':bool(np.isfinite(o).all()),
                'nan_count':int(np.isnan(o).sum()),
                'inf_count':int(np.isinf(o).sum())} for o in outputs]})
print(json.dumps({'manifest_sha256':hashlib.sha256((root/'freeze/manifest.json').read_bytes()).hexdigest(),
                  'role':role,'device_name':torch.cuda.get_device_name(),
                  'torch_version':torch.__version__,'cuda_version':torch.version.cuda,
                  'records':records},allow_nan=False))
"""
    result = subprocess.run(
        [sys.executable, "-c", program, str(root), json.dumps(payload["requests"]), role],
        cwd=root / "code",
        env=dict(
            os.environ,
            PYTHONPATH=str(root / "code"),
            CUBLAS_WORKSPACE_CONFIG=":4096:8",
            PYTHONDONTWRITEBYTECODE="1",
        ),
        capture_output=True,
        text=True,
        check=True,
        timeout=180,
    )
    response = json.loads(result.stdout)
    response["stderr"] = result.stderr[-4000:]
    response["diagnostic_program_sha256"] = hashlib.sha256(program.encode()).hexdigest()
    return response


def main(report_path, output, role="repaired"):
    from globus_compute_sdk import Client, Executor
    from globus_compute_sdk.serialize import ComputeSerializer, DillCodeSource

    sys.path.insert(0, str(ROOT / "docs/experiments/result-validity-audit-20261020"))
    from gpu_coordination import A100Lease

    report = read(report_path)
    if report["totals"]["pending_or_unverified_targets"]:
        raise ValueError("Complete the primary cohort first")
    groups = {}
    for target in report["targets"]:
        entry, summary = target["coverage"], target["summary"]
        cases = [
            c["case"]
            for c in summary["cases"]
            if c.get("observations", {}).get(role + "/fp16", {}).get("reason")
            in {
                "ValueError: Stateful or nondeterministic output",
                "ValueError: Wrong output size or nonfinite output",
            }
        ]
        if not cases:
            continue
        row = next(
            r
            for r in report["rows"]
            if r["repaired_source_sha256"] == entry["source_sha256"]
            and r["model"] == entry["model"]
            and r["candidate"] == entry["candidate"]
        )
        results = Path(row["evidence_results"])
        transport = read(results / "transport.json")
        group = groups.setdefault(
            transport["remote"], {"requests": {}, "manifest": summary["manifest_sha256"]}
        )
        assert group["manifest"] == summary["manifest_sha256"]
        group["requests"][entry["target"]] = cases
    executor = Executor(
        endpoint_id="b162a840-38b4-4c1a-84cc-579fb62f4dfc",
        client=Client(),
        serializer=ComputeSerializer(strategy_code=DillCodeSource()),
    )
    responses = []
    for root, group in groups.items():
        print(
            f"Inspecting {role}: {sum(map(len, group['requests'].values()))} cases in {root}",
            flush=True,
        )
        with A100Lease():
            response = executor.submit(
                inspect, {"root": root, "requests": group["requests"], "role": role}
            ).result(timeout=240)
        assert response["manifest_sha256"] == group["manifest"]
        responses.append({"remote": root, **response})
        write(
            output,
            {"diagnostic_only": True, "qualification_results_changed": False, "groups": responses},
        )
    print(
        f"Saved {sum(len(r['records']) for r in responses)} repeatability diagnostics", flush=True
    )
    import os

    sys.stdout.flush()
    os._exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--role", choices=("baseline", "repaired"), default="repaired")
    args = parser.parse_args()
    main(args.report.resolve(), args.output.resolve(), args.role)
