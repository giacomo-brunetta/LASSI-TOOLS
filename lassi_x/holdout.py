"""Independent, opt-in C differential holdout; never imported by the repair loop.

Preparation reads artifacts only. Evaluation executes frozen C and Torch sources.
The candidate's input builder is never used to generate holdout inputs or oracles.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

import numpy as np
import yaml

from .c_inputs import SCIENCE, instrument_reference
from .input_contract import _binding, compare_input_arrays, load_contract
from .validation import scrape_polybench_dump

SUPPORTED = {
    "direct-dft",
    "jpeg-dct",
    "lorenz-rk4",
    "low-rank-compression",
    "poisson-cg",
    "softened-nbody",
    "wavelet-compression",
    "iir-filter-bank",
    "polybench-3mm",
    "polybench-atax",
    "polybench-bicg",
    "polybench-cholesky",
    "polybench-covariance",
    "polybench-deriche",
    "polybench-gemver",
    "polybench-gesummv",
    "polybench-jacobi-2d",
    "polybench-lu",
    "polybench-trmm",
}
HARNESS_FILES = (
    "holdout.py",
    "c_inputs.py",
    "input_contract.py",
    "validation.py",
    "candidate_runner.py",
    "precision_audit_worker.py",
)


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(campaign: Path, output: Path, spec: Path) -> None:
    """Freeze terminal recovered sources, references and schemas without executing them."""
    if output.exists():
        raise ValueError("Use a new output directory; a holdout freeze cannot be overwritten")
    policy = read(spec)
    if policy["protocol"] != "accuracy-holdout-v1" or len(policy["cases"]) < 12:
        raise ValueError("Expected accuracy-holdout-v1 with at least twelve cases")
    if len({c["name"] for c in policy["cases"]}) != len(policy["cases"]):
        raise ValueError("Duplicate holdout case names")
    # Inspect every terminal record, including unsuccessful trials in the inventory.
    inventory, targets = [], []
    for record in sorted(campaign.glob("*/*/*/repair.json")):
        result = read(record)
        row, variant = result["row"], result.get("variant") or {}
        entry = {k: row[k] for k in ("model", "kernel", "candidate", "precision")}
        entry.update(record=str(record.resolve()), record_sha256=sha(record))
        recovered = variant.get("recovered") is True
        entry["disposition"] = "selected" if recovered else "not_recovered"
        inventory.append(entry)
        if not recovered or result.get("interrupted"):
            entry["disposition"] = "interrupted" if result.get("interrupted") else "not_recovered"
            continue
        kernel = row["kernel"]
        if kernel not in SUPPORTED:
            entry["disposition"] = "unsupported_adapter"
            continue
        config = yaml.safe_load((record.parent / "config.yaml").read_text())
        project = Path(config["project"]["root"])

        def resolve(value: str, base: Path = project) -> Path:
            path = Path(value)
            return path if path.is_absolute() else base / path

        baseline_record = Path(result["baseline_record"])
        baseline = baseline_record.parent / "candidate.py"
        repaired = Path(variant["module_path"])
        measurements = variant.get("target_measurements", variant.get("measurements", []))
        final_measurement: dict[str, Any] = next(
            (m for m in reversed(measurements) if m.get("precision") == row["precision"]),
            {},
        )
        if final_measurement.get("status") != "ok" or sha(repaired) != final_measurement.get(
            "source_hash"
        ):
            raise ValueError(f"Recovered source does not match its measurements: {record}")
        if sha(baseline) != read(baseline_record)["source_sha256"]:
            raise ValueError(f"Baseline source changed: {baseline}")
        dataset = (
            config["measure"].get("evaluation_dataset")
            or config["measure"].get("performance_dataset")
            or config["kernel"]["validation_dataset"]
        )
        check = config["arena"]["input_check"]
        contract = resolve(check["contracts"][dataset])
        arrays, metadata = load_contract(contract)
        if metadata["kernel"] != kernel or metadata["dataset"] != dataset:
            raise ValueError("Contract kernel or workload mismatch")
        fixture = baseline.parent / "c-inputs.npz"
        with np.load(fixture, allow_pickle=False) as archive:
            schema = json.loads(str(archive["__lassi_input_schema__"].item()))
            actual = {s["argument"]: archive[s["argument"]] for s in schema}
        bindings = check.get("bindings", {})
        parity = compare_input_arrays(actual, arrays, metadata, bindings=bindings)
        if not parity["ok"]:
            raise ValueError(f"Baseline schema lacks trusted input parity: {parity['errors']}")
        folder = output / row["model"] / kernel / f"{row['candidate']}-{row['precision']}"
        folder.mkdir(parents=True)
        shutil.copy2(contract, folder / "contract.npz")
        shutil.copy2(baseline, folder / "baseline.py")
        shutil.copy2(repaired, folder / "repaired.py")
        write(folder / "schema.json", schema)
        # Keep quoted includes and configured build flags. Hash all build dependencies.
        reference = resolve(config["kernel"]["reference"])
        if metadata.get("source_sha256") != sha(reference):
            raise ValueError(f"C reference differs from the input contract: {reference}")
        dependencies = {reference, *reference.parent.glob("*.h")}
        dependencies.update(resolve(p) for p in config["kernel"].get("context", []))
        for token in config["oracle"]["build"]:
            if Path(token).is_file():
                dependencies.add(Path(token).resolve())
            if token.startswith("-I") and Path(token[2:]).is_dir():
                dependencies.update(Path(token[2:]).glob("*.h"))
        dependency_files = {}
        for dependency in sorted(dependencies):
            parent_id = hashlib.sha256(str(dependency.parent).encode()).hexdigest()[:12]
            destination = folder / "references" / parent_id / dependency.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dependency, destination)
            dependency_files[str(dependency.resolve())] = str(destination.relative_to(folder))
        write(
            folder / "target.json",
            {
                **entry,
                "dataset": dataset,
                "bindings": bindings,
                "reference": str(reference),
                "build": config["oracle"]["build"],
                "project": str(project),
                "capture": config["oracle"]["capture"],
                "format": config["oracle"]["format"],
                "timeout_s": config["oracle"].get("timeout_s", 3600),
                "scalar_shapes": {s["argument"]: list(actual[s["argument"]].shape) for s in schema},
                "dependencies": {str(p.resolve()): sha(p) for p in dependencies},
                "dependency_files": dependency_files,
            },
        )
        targets.append(str((folder / "target.json").relative_to(output)))
    output.mkdir(parents=True, exist_ok=True)
    harness_hashes = {}
    for name in HARNESS_FILES:
        path = Path(__file__).with_name(name)
        destination = output / "harness" / name
        destination.parent.mkdir(exist_ok=True)
        shutil.copy2(path, destination)
        harness_hashes[name] = sha(path)
    write(output / "policy.json", policy)
    write(output / "inventory.json", inventory)
    write(
        output / "manifest.json",
        {
            "protocol": policy["protocol"],
            "status": "prepared_not_evaluated",
            "campaign": str(campaign.resolve()),
            "harness_sha256": harness_hashes,
            "targets": targets,
            "files": {
                str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()
            },
        },
    )


def make_case(
    original: dict[str, np.ndarray], metadata: dict[str, Any], case: dict[str, Any]
) -> dict[str, np.ndarray]:
    """Same-size, domain-preserving interventions, independent across data fields."""
    arrays = {k: v.copy() for k, v in original.items()}
    kernel = metadata["kernel"]
    rng = np.random.default_rng(case["seed"])
    family, amount = case["family"], case["amount"]
    for key in sorted(metadata["required"]):
        a = arrays[key]
        if not a.shape or key in metadata.get("integer_fields", []):
            continue  # Fixed dimensions, step counts, coefficients and scalar parameters.
        scale = max(float(np.sqrt(np.mean(a * a))), 1e-3)
        noise = rng.uniform(-1, 1, a.shape)
        if kernel in {"polybench-cholesky", "polybench-lu"} and key == "A":
            # D A D + positive diagonal preserves SPD without cubic generation work.
            diagonal = np.asarray(rng.uniform(0.75, 1.25, a.shape[0]))
            if family == "independent":
                b = rng.uniform(-0.25, 0.25, a.shape)
                b = (b + b.T) / 2
                np.fill_diagonal(b, np.abs(b).sum(axis=1) + 1)
                arrays[key] = b
            elif family == "scale":
                arrays[key] = a * amount
            else:
                arrays[key] = (
                    diagonal[:, None] * a * diagonal[None, :] + np.eye(a.shape[0]) * scale * amount
                )
            continue
        if family == "local":
            value = a + scale * amount * noise
        elif family == "independent":
            # Distinct offset and cancellation regimes, with independent fields.
            value = scale * (0.75 + 0.25 * noise) if case["seed"] % 2 else scale * noise
        elif family == "scale":
            value = a * amount
        elif family == "structured":
            grid = sum(
                (axis + 1) * indices
                for axis, indices in enumerate(np.ogrid[tuple(slice(0, n) for n in a.shape)])
            )
            value = a + amount * scale * np.sin(0.731 * grid + rng.uniform(0, 6))
        elif family == "sparse":
            value = a + scale * amount * noise * (rng.random(a.shape) < 0.01)
        else:
            raise ValueError(f"Unknown holdout family: {family}")
        if kernel == "softened-nbody" and key == "mass":
            value = np.maximum(np.abs(value), scale * 0.01)
        if kernel == "polybench-trmm" and key == "A":
            value = np.tril(value)
            np.fill_diagonal(value, 1.0)
        arrays[key] = np.ascontiguousarray(value)
    # Reestablish dependent *initial* state; no reference computation occurs here.
    if kernel == "poisson-cg":
        arrays["p"] = arrays["r"].copy()
        arrays["rr"] = np.asarray(np.sum(arrays["r"] ** 2))
    if kernel == "low-rank-compression":
        arrays["residual"] = arrays["image"].copy()
    if kernel == "wavelet-compression":
        arrays["coefficients"] = arrays["image"].copy()
    return arrays


def injected_reference(
    source: str, kernel: str, arrays: dict[str, np.ndarray]
) -> tuple[str, list[str]]:
    """Insert stdin loads at the trusted boundary; preserve the C computation verbatim."""
    captured, _ = instrument_reference(source, kernel)
    boundary = captured.index("\n/* LASSI trusted pre-computation input capture. */")
    code, fields = ["\n/* Holdout input injection; original computation follows. */\n"], []
    for key, array in arrays.items():
        if not array.shape and not (kernel == "poisson-cg" and key == "rr"):
            continue
        fields.append(key)
        rank = len(array.shape)
        for i, n in enumerate(array.shape):
            code.append(f"for (int lassi_h{i}=0; lassi_h{i}<{n}; ++lassi_h{i}) {{\n")
        base = f"(POLYBENCH_ARRAY({key}))" if rank and kernel not in SCIENCE else key
        destination = base + "".join(f"[lassi_h{i}]" for i in range(rank))
        code.append("{ double lassi_value;\n")
        code.append("if (fread(&lassi_value, sizeof(double), 1, stdin)!=1) return 71;\n")
        code.append(f"{destination} = lassi_value; }}\n")
        code.extend("}\n" for _ in range(rank))
    return "#include <stdio.h>\n" + source[:boundary] + "".join(code) + source[boundary:], fields


def run_command(
    command: list[str], folder: Path, timeout: float, data: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        command, cwd=folder, input=data, capture_output=True, timeout=timeout, check=False
    )
    if result.returncode:
        stderr = result.stderr.decode(errors="replace")[-4000:]
        raise RuntimeError(f"Command failed ({result.returncode}): {stderr}")
    return result


def c_output(
    target: dict[str, Any],
    executable: Path,
    fields: list[str],
    arrays: dict[str, np.ndarray],
    folder: Path,
) -> tuple[np.ndarray, list[int]]:
    payload = b"".join(np.ascontiguousarray(arrays[k], dtype=np.float64).tobytes() for k in fields)
    result = run_command([str(executable)], folder, target["timeout_s"], payload)
    text = (result.stderr if target["capture"] == "stderr" else result.stdout).decode()
    if target["format"] == "polybench":
        # Match the campaign oracle's explicit dump envelope. FDTD's trusted
        # reference prints additional diagnostic arrays after END DUMP_ARRAYS;
        # those are outside its established exported output contract.
        start = text.find("==BEGIN DUMP_ARRAYS==")
        end = text.find("==END", start + 1)
        if start >= 0 and end > start:
            text = text[start:end]
        # Use C dump boundaries, independent of how a candidate packs its outputs.
        blocks = re.findall(r"begin dump: [^\n]+\n(.*?)end   dump:", text, re.S)
        if not blocks:
            raise ValueError("C output has no named dump blocks")
        components = [scrape_polybench_dump(block) for block in blocks]
        flat = np.concatenate(components)
        sizes = [c.size for c in components]
    else:
        flat = np.fromstring(text.replace(",", " "), sep=" ")
        sizes = [flat.size]
        if target["kernel"] in {"jpeg-dct", "wavelet-compression", "low-rank-compression"}:
            sizes = [arrays["image"].size, 1, 1]
    if not flat.size or not np.isfinite(flat).all() or sum(sizes) != flat.size:
        raise ValueError("Invalid C output; this case is unverified")
    return flat, sizes


def input_values(
    arrays: dict[str, np.ndarray], schema: list[dict[str, Any]], target: dict[str, Any]
) -> list[np.ndarray]:
    values = []
    for s in schema:
        name = s["argument"]
        binding = target["bindings"].get(name) or _binding(name, target["kernel"], arrays)
        if binding:
            value = arrays[binding[:-2]].T if binding.endswith(".T") else arrays[binding]
        elif target["kernel"] == "polybench-gesummv" and name == "M":
            value = np.stack([arrays["A"], arrays["B"]])
        elif target["kernel"] == "polybench-doitgen" and name == "weight":
            value = arrays["C4"].T
        else:
            raise ValueError(f"No trusted input binding for {name}")
        shape = s.get("shape", target.get("scalar_shapes", {}).get(name, []))
        squeezed_shape = tuple(n for n in shape if n != 1)
        if np.squeeze(value).shape != squeezed_shape:
            raise ValueError(f"Unreviewed input layout: {name}")
        values.append(value.reshape(shape).copy())
    return values


def metrics(actual: np.ndarray, expected: np.ndarray, sizes: list[int]) -> dict[str, Any]:
    if (
        actual.shape != expected.shape
        or not np.isfinite(actual).all()
        or not sizes
        or sum(sizes) != expected.size
        or min(sizes) < 1
    ):
        raise ValueError("Wrong output size or nonfinite output")
    errors, offset = [], 0
    for size in sizes:
        left, right = actual[offset : offset + size], expected[offset : offset + size]
        errors.append(
            float(np.linalg.norm(left - right) / max(float(np.linalg.norm(right)), 1e-30))
        )
        offset += size
    return {
        "relative_l2": max(errors),
        "component_relative_l2": errors,
        "max_abs_error": float(np.max(np.abs(actual - expected))),
    }


def evaluate(manifest_path: Path, target_path: Path, results: Path, device: str) -> bool:
    """Explicit evaluation entry point. Use the destination Torch environment."""
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch  # noqa: PLC0415

    from .candidate_runner import PRECISIONS, load_module  # noqa: PLC0415
    from .precision_audit_worker import TargetDtypeAudit  # noqa: PLC0415

    manifest = read(manifest_path)
    root = manifest_path.parent
    for name, expected_hash in manifest.get("harness_sha256", {}).items():
        if sha(Path(__file__).with_name(name)) != expected_hash:
            raise ValueError(f"Installed holdout harness changed: {name}")
    if str(target_path.resolve().relative_to(root.resolve())) not in manifest["targets"]:
        raise ValueError("Target is absent from the frozen manifest")
    for path, expected_hash in manifest["files"].items():
        if sha(root / path) != expected_hash:
            raise ValueError(f"Frozen holdout artifact changed: {path}")
    target, policy = read(target_path), read(root / "policy.json")
    frozen_paths = {
        old: (target_path.parent / relative).resolve()
        for old, relative in target.get("dependency_files", {}).items()
    }
    for path, expected_hash in target["dependencies"].items():
        if sha(frozen_paths.get(path, Path(path))) != expected_hash:
            raise ValueError(f"C reference dependency changed: {path}")
    results.mkdir(parents=True, exist_ok=False)
    original, metadata = load_contract(target_path.parent / "contract.npz")
    schema = read(target_path.parent / "schema.json")
    reference_path = frozen_paths.get(target["reference"], Path(target["reference"]))
    generated, fields = injected_reference(reference_path.read_text(), target["kernel"], original)
    replacements = {old: str(new) for old, new in frozen_paths.items()}
    replacements.update(
        {str(Path(old).parent): str(new.parent) for old, new in frozen_paths.items()}
    )

    def relocate(value: str) -> str:
        for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
            value = value.replace(old, new)
        return value

    generated = relocate(generated)
    source, executable = results / "reference.c", results / "reference"
    source.write_text(generated)
    substitutions = {
        "reference": str(source.resolve()),
        "oracle_dir": str(results.resolve()),
        "project": target["project"],
        "input": "",
        "output": str(results / "unused.csv"),
    }
    build = [relocate(part.format(**substitutions)) for part in target["build"]]
    build.append(f"-I{reference_path.parent}")
    write(results / "build-command.json", build)
    compiler_version = run_command([build[0], "--version"], results, 30)
    (results / "compiler-version.txt").write_bytes(compiler_version.stdout)
    compiled = run_command(build, results, target["timeout_s"])
    (results / "build.stderr").write_bytes(compiled.stderr)
    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    # Some CUDA operations lack an implementation certified by this Torch
    # version. Request deterministic implementations where available, and
    # enforce observed repeatability below for every executed forward.
    torch.use_deterministic_algorithms(True, warn_only=True)
    modules = {
        role: load_module(target_path.parent / f"{role}.py") for role in ("baseline", "repaired")
    }
    cases = [{"name": "canonical_control", "family": "control"}, *policy["cases"]]
    records = []
    for case in cases:
        folder = results / case["name"]
        folder.mkdir()
        arrays = original if case["family"] == "control" else make_case(original, metadata, case)
        np.savez(folder / "inputs.npz", **cast("dict[str, Any]", arrays))
        record: dict[str, Any] = {
            "case": case["name"],
            "holdout": case["family"] != "control",
            "observations": {},
        }
        try:
            reference, sizes = c_output(target, executable.resolve(), fields, arrays, folder)
            repeated, repeated_sizes = c_output(
                target, executable.resolve(), fields, arrays, folder
            )
            if sizes != repeated_sizes or not np.array_equal(reference, repeated):
                raise ValueError("C reference is nondeterministic")
            np.save(folder / "reference.npy", reference)
            # Secondary diagnostic: C on rounded arrays and mutable CG state.
            # Fixed C scalars retain their original values. This is diagnostic,
            # never a substitute for acceptance against the unrounded C inputs.
            target_dtype = PRECISIONS[target["precision"]]
            rounded = {
                name: (
                    torch.from_numpy(value.copy()).to(target_dtype).double().numpy()
                    if name in fields and name not in metadata.get("integer_fields", [])
                    else value.copy()
                )
                for name, value in arrays.items()
            }
            rounded_reference = None
            try:
                if not all(np.isfinite(value).all() for value in rounded.values()):
                    raise ValueError("Input arrays are not target-representable")
                rounded_output, rounded_sizes = c_output(
                    target, executable.resolve(), fields, rounded, folder
                )
                if rounded_sizes != sizes:
                    raise ValueError("Rounded-input C output layout changed")
                rounded_reference = rounded_output
                np.save(folder / "rounded-input-reference.npy", rounded_reference)
                record["input_rounding_error"] = metrics(rounded_reference, reference, sizes)
            except Exception as exc:
                record["input_rounding_error"] = {"status": "unverified", "reason": str(exc)}
            values = input_values(arrays, schema, target)
            for role, module in modules.items():
                for precision in ("fp64", "fp32", target["precision"]):
                    observation: dict[str, Any] = {}
                    key = f"{role}/{precision}"
                    try:
                        dtype = PRECISIONS[precision]
                        model = module.make_model().to(device=device, dtype=dtype).eval()

                        def inputs(
                            case_values: list[np.ndarray] = values, input_dtype: Any = dtype
                        ) -> tuple[Any, ...]:
                            items = []
                            for value, s in zip(case_values, schema, strict=True):
                                if s["kind"] != "tensor":
                                    items.append(
                                        {"int": int, "float": float, "bool": bool}[s["kind"]](
                                            value.item()
                                        )
                                    )
                                else:
                                    chosen = (
                                        getattr(torch, s["integer_dtype"])
                                        if s["integer_dtype"]
                                        else input_dtype
                                    )
                                    item = torch.empty_strided(
                                        tuple(s["shape"]),
                                        tuple(s["stride"]),
                                        dtype=chosen,
                                        device=device,
                                    )
                                    item.copy_(
                                        torch.from_numpy(value).to(device=device, dtype=chosen)
                                    )
                                    if not torch.isfinite(item).all():
                                        raise ValueError(
                                            "Input is not representable in the target format"
                                        )
                                    items.append(item)
                            return tuple(items)

                        def forward(
                            instance: Any = model,
                            arithmetic_dtype: Any = dtype,
                            audited: bool = precision in {"fp16", "bf16"},
                            input_factory: Any = inputs,
                        ) -> np.ndarray:
                            supplied = input_factory()
                            before = [
                                v.clone() if isinstance(v, torch.Tensor) else v for v in supplied
                            ]
                            audit = TargetDtypeAudit(arithmetic_dtype)
                            if audited:
                                audit.check(supplied, "supplied inputs")
                            with (
                                torch.inference_mode(),
                                audit if audited else contextlib.nullcontext(),
                            ):
                                output = instance(*supplied)
                            if audited:
                                audit.check(output, "forward output")
                            if audit.violations:
                                raise ValueError(
                                    f"Explicit arithmetic dtype violation: {audit.violations}"
                                )
                            if any(
                                isinstance(v, torch.Tensor) and not torch.equal(v, b)
                                for v, b in zip(supplied, before, strict=True)
                            ):
                                raise ValueError("Forward mutated supplied input")
                            parts = output if isinstance(output, (tuple, list)) else (output,)
                            if not parts or not all(isinstance(p, torch.Tensor) for p in parts):
                                raise ValueError("Unsupported output structure")
                            return np.concatenate(
                                [p.detach().double().cpu().numpy().reshape(-1) for p in parts]
                            )

                        first, second = forward(), forward()
                        if not np.array_equal(first, second):
                            raise ValueError("Stateful or nondeterministic output")
                        observation.update(metrics(first, reference, sizes))
                        if precision == target["precision"] and rounded_reference is not None:
                            observation["against_rounded_input_C"] = metrics(
                                first, rounded_reference, sizes
                            )
                        # C MSE / relative residual and count outputs are nonnegative.
                        if target["kernel"] in {
                            "jpeg-dct",
                            "wavelet-compression",
                            "low-rank-compression",
                        } and np.any(first[-2:] < 0):
                            raise ValueError("Negative error metric or count")
                        passed = (
                            bool(
                                np.allclose(
                                    first,
                                    reference,
                                    rtol=policy["fp64_rtol"],
                                    atol=policy["fp64_atol"],
                                )
                            )
                            if precision == "fp64"
                            else observation["relative_l2"] <= policy["relative_l2_limit"]
                        )
                        observation.update(status="pass" if passed else "fail")
                        np.save(folder / f"{role}-{precision}.npy", first)
                    except Exception as exc:
                        observation.update(
                            status="unverified", reason=f"{type(exc).__name__}: {exc}"
                        )
                    record["observations"][key] = observation
            repair = record["observations"][f"repaired/{target['precision']}"]
            base = record["observations"][f"baseline/{target['precision']}"]
            record["passed"] = all(
                record["observations"][k]["status"] == "pass"
                for k in ("repaired/fp64", "repaired/fp32", f"repaired/{target['precision']}")
            )
            record["baseline_passed"] = base["status"] == "pass"
            record["baseline_semantics_valid"] = (
                record["observations"]["baseline/fp64"]["status"] == "pass"
            )
            record["repaired_relative_l2"] = repair.get("relative_l2")
            record["regressed_from_healthy_baseline"] = (
                base["status"] == "pass" and repair["status"] != "pass"
            )
        except Exception as exc:
            record.update(passed=False, status="unverified", reason=f"{type(exc).__name__}: {exc}")
        records.append(record)
        write(folder / "result.json", record)
    holdout = [r for r in records if r["holdout"]]
    passed = all(r["passed"] for r in records) and len(holdout) == len(policy["cases"])
    holdout_errors = [
        r["repaired_relative_l2"] for r in holdout if r.get("repaired_relative_l2") is not None
    ]
    write(
        results / "summary.json",
        {
            "protocol": policy["protocol"],
            "target": target,
            "manifest_sha256": sha(manifest_path),
            "device": device,
            "torch_version": torch.__version__,
            "numpy_version": np.__version__,
            "python_version": sys.version,
            "determinism": {
                "algorithms": "requested_warn_only",
                "acceptance": "two forward outputs must be bitwise equal",
                "cublas_workspace_config": os.environ["CUBLAS_WORKSPACE_CONFIG"],
            },
            "cuda_version": torch.version.cuda,
            "device_name": torch.cuda.get_device_name() if device.startswith("cuda") else "cpu",
            "passed": passed,
            "holdout_cases": len(holdout),
            "holdout_passes": sum(r["passed"] for r in holdout),
            "worst_holdout_relative_l2": max(holdout_errors, default=None),
            "failed_cases": [r["case"] for r in records if not r["passed"]],
            "cases": records,
            "interpretation": (
                "Independent same-size differential evidence; "
                "no repair feedback or universal semantic certification."
            ),
        },
    )
    return passed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser(
        "prepare", help="Freeze sources only; execute no C or candidate code"
    )
    prepare_parser.add_argument("--campaign", type=Path, required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--spec", type=Path, required=True)
    for name in ("evaluate", "_worker"):
        evaluate_parser = commands.add_parser(name, help="Execute one frozen target")
        evaluate_parser.add_argument("--manifest", type=Path, required=True)
        evaluate_parser.add_argument("--target", type=Path, required=True)
        evaluate_parser.add_argument("--results", type=Path, required=True)
        evaluate_parser.add_argument("--device", choices=("cpu", "cuda"), required=True)
        evaluate_parser.add_argument("--timeout-s", type=float, default=86400)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    if args.command == "prepare":
        prepare(args.campaign.resolve(), args.output.resolve(), args.spec.resolve())
        return 0
    if args.command == "evaluate":
        if args.results.exists():
            raise ValueError("Use a fresh results directory")
        command = [
            sys.executable,
            "-m",
            "lassi_x.holdout",
            "_worker",
            "--manifest",
            str(args.manifest.resolve()),
            "--target",
            str(args.target.resolve()),
            "--results",
            str(args.results.resolve()),
            "--device",
            args.device,
        ]
        # A stuck Python forward or C descendant must not survive a target timeout.
        process = subprocess.Popen(command, start_new_session=True)
        try:
            return process.wait(timeout=args.timeout_s)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            write(
                args.results / "timeout.json",
                {
                    "status": "unverified",
                    "passed": False,
                    "reason": "target timeout",
                    "timeout_s": args.timeout_s,
                },
            )
            return 1
    return (
        0
        if evaluate(
            args.manifest.resolve(), args.target.resolve(), args.results.resolve(), args.device
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
