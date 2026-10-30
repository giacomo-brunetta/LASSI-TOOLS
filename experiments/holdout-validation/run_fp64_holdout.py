"""Twenty supplied-input C differential checks for accepted CPU translations.

Uses the frozen main comparison cohort, including historically accepted sources
subsequently held by audits. Does not generate or repair any candidate.
"""
# ruff: noqa: E402, PLC0415

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import hashlib
import inspect
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from lassi_x import holdout as h
from lassi_x.c_inputs import build_input_contract
from lassi_x.config import RunConfig
from lassi_x.input_contract import _binding, load_contract


def cases():
    # Fresh seeds; five families, four cases each. Scale cases are distinct.
    return [
        dict(
            name=f"{family}_{i + 1}",
            family=family,
            seed=310000019 + j * 100003 + i * 7919,
            amount=amount,
        )
        for j, (family, amounts) in enumerate(
            [
                ("local", [0.01, 0.05, 0.1, 0.2]),
                ("independent", [1.0, 1.0, 1.0, 1.0]),
                ("scale", [0.25, 0.5, 1.5, 2.0]),
                ("structured", [0.1, 0.25, 0.5, 1.0]),
                ("sparse", [0.1, 0.25, 0.5, 1.0]),
            ]
        )
        for i, amount in enumerate(amounts)
    ]


def make_case(original, metadata, case):
    arrays = h.make_case(original, metadata, case)
    kernel = metadata["kernel"]
    rng = np.random.default_rng(case["seed"])
    if kernel == "polybench-nussinov":
        arrays["seq"] = rng.integers(0, 4, original["seq"].shape).astype(float)
    elif kernel == "polybench-floyd-warshall":
        arrays["path"] = rng.integers(1, 100, original["path"].shape).astype(float)
        np.fill_diagonal(arrays["path"], 0)
    elif kernel == "mutual-information":
        joint = (
            original["joint"] ** case["amount"]
            if case["family"] == "scale"
            else np.maximum(np.abs(arrays["joint"]), 1e-15)
        )
        arrays["joint"] = joint / joint.sum()
    if case["family"] == "sparse":
        for key in metadata["required"]:
            if (
                original[key].shape
                and key not in metadata.get("integer_fields", [])
                and np.array_equal(arrays[key], original[key])
            ):
                index = tuple(int(rng.integers(n)) for n in original[key].shape)
                if kernel == "polybench-trmm" and key == "A":
                    index = (1, 0)
                arrays[key][index] += (
                    max(float(np.sqrt(np.mean(original[key] ** 2))), 0.001) * case["amount"]
                )
    if kernel == "mutual-information":
        arrays["joint"] /= arrays["joint"].sum()
    # A forced sparse intervention may have changed the independent data after
    # the shared case generator established dependent initial state.
    if kernel == "poisson-cg":
        arrays["p"] = arrays["r"].copy()
        arrays["rr"] = np.asarray(np.sum(arrays["r"] ** 2))
    elif kernel == "low-rank-compression":
        arrays["residual"] = arrays["image"].copy()
    elif kernel == "wavelet-compression":
        arrays["coefficients"] = arrays["image"].copy()
    if all(np.array_equal(arrays[k], original[k]) for k in original):
        raise ValueError("Holdout did not change any input")
    return arrays


def bind_inputs(module, original, kernel, dataset):
    import torch

    kwargs = dict(device="cpu", dtype=torch.float64)
    if "dataset" in inspect.signature(module.build_inputs).parameters:
        kwargs["dataset"] = dataset
    template = module.build_inputs(**kwargs)
    model = module.make_model().to(device="cpu", dtype=torch.float64).eval()
    names = list(inspect.signature(model.forward).parameters)
    positional = {
        "polybench-3mm": ["A", "B", "C", "D"],
        "poisson-cg": ["x", "r", "p", "ap", "rr"],
        "low-rank-compression": ["image", "residual", "approximation"],
    }
    if kernel in positional and len(names) == 1 and len(template) == len(positional[kernel]):
        names = positional[kernel]
    bindings = []
    aliases = {
        "polybench-3mm": dict(zip(("a", "b", "c", "d"), ("A", "B", "C", "D"), strict=True)),
        "polybench-deriche": {"image": "imgIn", "input": "imgIn"},
        "mutual-information": {"p": "joint", "joint_prob": "joint"},
    }
    for name, value in zip(names, template, strict=True):
        key = _binding(name, kernel, original) or aliases.get(kernel, {}).get(name.lower())
        if key is not None:

            def transform(a, key=key):
                return a[key]
        elif kernel == "polybench-gesummv" and name.lower() == "m":

            def transform(a):
                return np.stack([a["A"], a["B"]])
        elif kernel == "polybench-doitgen" and name.lower() == "weight":

            def transform(a):
                return a["C4"].T
        elif (
            np.size(value.detach().cpu().numpy() if isinstance(value, torch.Tensor) else value) == 1
        ):
            # Fixed scalar interface parameters; recorded for review below.
            constant = (
                value.detach().cpu().numpy().copy()
                if isinstance(value, torch.Tensor)
                else np.asarray(value)
            )

            def transform(a, constant=constant):
                return constant
        else:
            raise ValueError(
                f"Unreviewed input binding: {name}, shape={getattr(value, 'shape', None)}"
            )
        bindings.append((name, value, transform))

    def factory(arrays):
        values = []
        for name, template, transform in bindings:
            array = np.asarray(transform(arrays))
            shape = tuple(template.shape) if isinstance(template, torch.Tensor) else ()
            if np.squeeze(array).shape != tuple(n for n in shape if n != 1):
                raise ValueError(f"Unreviewed layout for {name}: {array.shape} -> {shape}")
            if isinstance(template, torch.Tensor):
                value = torch.empty_strided(shape, template.stride(), dtype=template.dtype)
                value.copy_(torch.as_tensor(array.copy().reshape(shape), dtype=template.dtype))
            else:
                value = type(template)(array.item())
            values.append(value)
        return tuple(values)

    descriptions = [
        dict(
            argument=n,
            shape=list(v.shape) if isinstance(v, torch.Tensor) else [],
            canonical_value=np.asarray(f(original)).tolist() if np.size(f(original)) == 1 else None,
        )
        for n, v, f in bindings
    ]
    return model, factory, descriptions


def worker(job, output):
    import torch

    from lassi_x.candidate_runner import load_module

    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True, warn_only=True)
    rows = h.read(job)
    folder = output.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    config = RunConfig.load(ROOT / Path(rows[0]["run"]).parent / "resolved-config.yaml")
    contract = asyncio.run(build_input_contract(config, folder / "capture"))
    original, metadata = load_contract(contract)
    kernel = rows[0]["kernel"]
    source = config.resolve_project_path(config.kernel.reference)
    injected = original
    if kernel == "iir-filter-bank":
        # C filter coefficients are const and remain fixed in this experiment.
        injected = {"signal": original["signal"]}
    generated, fields = h.injected_reference(source.read_text(), kernel, injected)
    reference = folder / "reference.c"
    reference.write_text(generated)
    substitutions = dict(
        reference=str(reference),
        oracle_dir=str(folder),
        project=str(config.project.root),
        input="",
        output=str(folder / "unused.csv"),
    )
    build = [x.format(**substitutions) for x in config.oracle.build] + [f"-I{source.parent}"]
    h.write(folder / "build-command.json", build)
    (folder / "compiler-version.txt").write_bytes(
        h.run_command([build[0], "--version"], folder, 30).stdout
    )
    h.write(
        folder / "environment.json",
        dict(
            python=sys.version,
            torch=torch.__version__,
            numpy=np.__version__,
            device="cpu",
            threads=1,
        ),
    )
    h.write(
        folder / "reference-provenance.json",
        dict(
            source=str(source),
            source_sha256=h.sha(source),
            config_sha256=h.sha(ROOT / Path(rows[0]["run"]).parent / "resolved-config.yaml"),
        ),
    )
    h.run_command(build, folder, 120)
    target = dict(
        kernel=kernel, capture=config.oracle.capture, format=config.oracle.format, timeout_s=120
    )
    references = []
    seen_inputs = set()
    for case in [dict(name="canonical_control", family="control"), *cases()]:
        cf = folder / case["name"]
        cf.mkdir(exist_ok=True)
        try:
            arrays = (
                original if case["family"] == "control" else make_case(original, metadata, case)
            )
            fingerprint = hashlib.sha256(
                b"".join(np.ascontiguousarray(arrays[k]).tobytes() for k in sorted(arrays))
            ).hexdigest()
            if fingerprint in seen_inputs:
                raise ValueError("Duplicate holdout input")
            seen_inputs.add(fingerprint)
            np.savez(cf / "inputs.npz", **arrays)
            expected, sizes = h.c_output(target, folder / "reference", fields, arrays, cf)
            repeated, _ = h.c_output(target, folder / "reference", fields, arrays, cf)
            if not np.array_equal(expected, repeated):
                raise ValueError("C reference is nondeterministic")
            np.save(cf / "reference.npy", expected)
            references.append((case, arrays, expected, sizes, None))
        except Exception as exc:
            references.append((case, None, None, None, str(exc)))
    results = []
    for row in rows:
        record = {k: v for k, v in row.items() if k != "source"}
        candidate_dir = folder / row["candidate"]
        candidate_dir.mkdir(exist_ok=True)
        frozen = candidate_dir / "candidate.py"
        frozen.write_text(row["source"])
        if h.sha(frozen) != row["sha256"]:
            raise ValueError("Frozen source hash mismatch")
        observations = []
        try:
            module = load_module(frozen)
            model, factory, bindings = bind_inputs(
                module, original, kernel, config.kernel.validation_dataset
            )
            h.write(candidate_dir / "bindings.json", bindings)
            for case, arrays, expected, sizes, error in references:
                observation = dict(case=case["name"], status="unverified")
                try:
                    if error:
                        raise ValueError(error)

                    def forward(factory=factory, arrays=arrays, model=model):
                        supplied = factory(arrays)
                        before = [v.clone() if isinstance(v, torch.Tensor) else v for v in supplied]
                        with torch.inference_mode():
                            out = model(*supplied)
                        if any(
                            isinstance(v, torch.Tensor) and not torch.equal(v, b)
                            for v, b in zip(supplied, before, strict=True)
                        ):
                            raise ValueError("Forward mutated caller input")
                        parts = out if isinstance(out, (tuple, list)) else (out,)
                        return np.concatenate(
                            [p.detach().double().cpu().numpy().reshape(-1) for p in parts]
                        )

                    actual, repeated = forward(), forward()
                    if not np.array_equal(actual, repeated):
                        raise ValueError("Nondeterministic output")
                    observation.update(h.metrics(actual, expected, sizes))
                    passed = (
                        bool(np.array_equal(actual, expected))
                        if kernel in {"polybench-nussinov", "polybench-floyd-warshall"}
                        else bool(np.allclose(actual, expected, rtol=1e-10, atol=1e-12))
                    )
                    observation["status"] = "pass" if passed else "fail"
                    np.save(candidate_dir / f"{case['name']}.npy", actual)
                except Exception as exc:
                    observation["reason"] = f"{type(exc).__name__}: {exc}"
                observations.append(observation)
        except Exception as exc:
            observations = [
                dict(case=c["name"], status="unverified", reason=f"{type(exc).__name__}: {exc}")
                for c, *_ in references
            ]
        record.update(
            cases=observations,
            control_passed=observations[0]["status"] == "pass",
            holdout_passes=sum(o["status"] == "pass" for o in observations[1:]),
            qualified=all(o["status"] == "pass" for o in observations),
        )
        h.write(candidate_dir / "result.json", record)
        results.append(record)
        print(row["model"], kernel, row["candidate"], record["holdout_passes"], "/20", flush=True)
    h.write(folder / "results.json", results)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=ROOT / "docs/experiments/input-integrity-audit-20261020/main_campaign_sources.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    harness = {
        str(p.relative_to(ROOT)): h.sha(p)
        for p in [Path(__file__).resolve(), *sorted((ROOT / "lassi_x").rglob("*.py"))]
    }
    frozen_manifest = output / "harness-manifest.json"
    if frozen_manifest.exists() and h.read(frozen_manifest) != harness:
        raise ValueError("Harness changed; use a new output directory")
    h.write(frozen_manifest, harness)
    for relative in harness:
        destination = output / "harness" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    snapshot = h.read(args.snapshot)
    rows = [
        r
        for r in snapshot["sources"]
        if r["status"] == "ok" and (not args.only or r["kernel"] in args.only)
    ]
    h.write(
        output / "policy.json",
        dict(
            protocol="fp64-holdout-v1",
            cases=cases(),
            rtol=1e-10,
            atol=1e-12,
            integer_comparison="exact",
            canonical_control=True,
            scope=snapshot["scope"],
            snapshot_sha256=h.sha(args.snapshot),
        ),
    )
    groups = {}
    for row in rows:
        groups.setdefault((row["model"], row["kernel"]), []).append(row)

    def launch(item):
        (model, kernel), selected = item
        folder = output / model / kernel
        folder.mkdir(parents=True, exist_ok=True)
        if (folder / "results.json").exists():
            return
        job = folder / "job.json"
        h.write(job, selected)
        with (folder / "worker.log").open("w") as log:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--worker",
                        str(job),
                        "--output",
                        str(folder),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=900,
                )
                if result.returncode:
                    h.write(folder / "failure.json", dict(returncode=result.returncode))
            except subprocess.TimeoutExpired:
                h.write(folder / "failure.json", dict(reason="900 second group timeout"))

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        for _ in executor.map(launch, groups.items()):
            results = [r for p in output.glob("*/*/results.json") for r in h.read(p)]
            by_model = {
                m: dict(
                    candidates=len(rs),
                    control_passes=sum(r["control_passed"] for r in rs),
                    qualified=sum(r["qualified"] for r in rs),
                    holdout_passes=sum(r["holdout_passes"] for r in rs),
                    holdout_total=20 * len(rs),
                )
                for m in sorted({r["model"] for r in rows})
                if (rs := [r for r in results if r["model"] == m])
            }
            h.write(
                output / "summary.json",
                dict(
                    selected=len(rows),
                    completed=len(results),
                    by_model=by_model,
                    failed_groups=[
                        str(p.relative_to(output)) for p in output.glob("*/*/failure.json")
                    ],
                ),
            )
            print(f"Completed {len(results)}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
