"""Compile explicit C fixture entry points against pinned native dependencies.

No downloads or model calls occur here. ITK and RandLAPACK must have been built
under the declared native root; every invocation records its actual commands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import RunConfig

KINDS = {
    "rodinia/LavaMD": "lavamd",
    "rodinia/Myocyte": "myocyte",
    "rodinia/DWT2D": "dwt2d",
    "rodinia/CFD": "cfd",
    "npb-3.4.4/CG": "npb-cg",
    "npb-3.4.4/MG": "npb-mg",
    "npb-3.4.4/FT": "npb-ft",
    "itk/mutual-information": "mutual-information",
    "randlapack/randomized-svd": "randomized-svd",
    "parboil/mri-gridding": "mri-gridding",
}


def executable(name: str) -> str:
    result = shutil.which(name)
    if result is None:
        raise RuntimeError(f"Native workload compiler/tool missing: {name}")
    return result


def omp_include() -> Path:
    configured = os.environ.get("LASSI_OMP_INCLUDE")
    if configured:
        return Path(configured)
    # Apple Clang's header search does not include Homebrew's keg-only libomp.
    return Path("/opt/homebrew/opt/libomp/include")


def compile_reference(
    root: Path,
    native_root: Path,
    kind: str,
    reference: Path,
    output: Path,
    *,
    small_test: bool = False,
    extra_flags: list[str] | None = None,
) -> None:
    """Build one source revision, retaining the complete command record."""
    root, native_root = root.resolve(), native_root.resolve()
    output = output.resolve()
    directory = output.parent / "native-build"
    directory.mkdir(parents=True, exist_ok=False)
    fixture_root = root / "benchmarks/checks/native"
    commands: list[list[str]] = []

    def run(command: list[str], cwd: Path = directory) -> None:
        commands.append(command)
        (directory / "commands.json").write_text(json.dumps(commands, indent=2) + "\n")
        subprocess.run(command, cwd=cwd, check=True, timeout=1500)

    cc = executable("cc")
    flags = ["-O2", "-ffp-contract=off", f"-I{fixture_root}", *(extra_flags or [])]
    if kind in {"mutual-information", "randomized-svd", "cfd"}:
        command = [
            executable("cmake"),
            "-S",
            str(fixture_root),
            "-B",
            str(directory),
            f"-DLASSI_KIND={kind}",
            f"-DLASSI_ROOT={root}",
            f"-DLASSI_REFERENCE={reference}",
            f"-DLASSI_OUTPUT_DIRECTORY={output.parent}",
            f"-DLASSI_OMP_INCLUDE={omp_include()}",
            f"-DLASSI_SMALL_TEST={'ON' if small_test else 'OFF'}",
            "-DCMAKE_BUILD_TYPE=Release",
        ]
        if kind == "mutual-information":
            command.append(f"-DITK_DIR={native_root / 'itk-build'}")
        if kind == "randomized-svd":
            installs = native_root / "randnla/install"
            command.append(f"-DCMAKE_PREFIX_PATH={installs / 'RandLAPACK-install'}")
        run(command)
        run([executable("cmake"), "--build", str(directory), "--parallel", "2"])
        return
    if kind.startswith("npb-"):
        bench = kind[4:].upper()
        source_root = root / "benchmarks/npb-3.4.4/suites/NPB3.4.4/NPB3.4-OMP"
        config = directory.parent / "config"
        config.mkdir(exist_ok=True)
        (config / "make.def").write_text(
            "FC = gfortran\nFLINK = gfortran\nFFLAGS = -O2\nFLINKFLAGS = -O2\nRAND = randdp\n"
        )
        run([cc, str(source_root / "sys/setparams.c"), "-o", str(directory / "setparams")])
        run([str(directory / "setparams"), bench.lower(), "S" if small_test else "B"])
        original = (source_root / bench / f"{bench.lower()}.f90").read_text()
        match = re.search(r"^\s*subroutine\s+", original, re.MULTILINE | re.IGNORECASE)
        if match is None:
            raise ValueError("Pinned NPB source has no subroutine boundary")
        (directory / "routines.f90").write_text(original[match.start() :])
        if bench == "FT":
            block = (source_root / bench / "blk_par0.h").read_text().replace("=0", "=32")
            (directory / "blk_par.h").write_text(block)
        fc = executable("gfortran")
        fflags = [
            "-O2",
            "-ffp-contract=off",
            "-fallow-argument-mismatch",
            f"-I{directory}",
            f"-J{directory}",
        ]
        for name, source in [
            ("data", source_root / bench / f"{bench.lower()}_data.f90"),
            ("routines", directory / "routines.f90"),
            ("bridge", fixture_root / f"{kind}-bridge.f90"),
            ("random", source_root / "common/randdp.f90"),
            ("timers", source_root / "common/timers.f90"),
        ]:
            run([fc, *fflags, "-c", str(source), "-o", str(directory / f"{name}.o")])
        run(
            [cc, "-O2", "-c", str(source_root / "common/wtime.c"), "-o", str(directory / "wtime.o")]
        )
        if small_test:
            flags += {
                "CG": ["-DLASSI_CG_N=1400"],
                "MG": ["-DLASSI_MG_SIDE=32"],
                "FT": ["-DLASSI_FT_X=64", "-DLASSI_FT_Y=64", "-DLASSI_FT_Z=64"],
            }[bench]
        run([cc, "-std=c11", *flags, "-c", str(reference), "-o", str(directory / "entry.o")])
        run(
            [
                fc,
                *(
                    str(directory / (n + ".o"))
                    for n in (
                        "entry",
                        "data",
                        "routines",
                        "bridge",
                        "random",
                        "timers",
                        "wtime",
                    )
                ),
                "-lm",
                "-o",
                str(output),
            ]
        )
        return
    sources = [str(reference)]
    if kind in {"lavamd", "myocyte"}:
        flags += [f"-I{omp_include()}"]
        if os.uname().sysname == "Darwin":
            flags += ["-L/opt/homebrew/opt/libomp/lib", "-lomp"]
        else:
            flags += ["-fopenmp"]
    if kind == "lavamd":
        upstream = root / "benchmarks/rodinia/openmp/lavaMD"
        flags += [f"-I{upstream}", "-include", "sys/time.h"]
        sources += [str(upstream / "kernel/kernel_cpu.c"), str(upstream / "util/timer/timer.c")]
        if small_test:
            flags.append("-DLASSI_LAVA_SIDE=2")
    elif kind == "myocyte":
        flags += [f"-I{root / 'benchmarks/rodinia/openmp/myocyte'}"]
        sources.append(str(fixture_root / "myocyte-bridge.c"))
        if small_test:
            flags += ["-DLASSI_MYO_CELLS=2", "-DLASSI_MYO_STEPS=4"]
    elif kind == "mri-gridding":
        upstream = root / "benchmarks/parboil/benchmarks/mri-gridding/src/base"
        flags += [f"-I{upstream}"]
        sources.append(str(upstream / "CPU_kernels.c"))
        if small_test:
            flags += ["-DLASSI_GRID_SIDE=16", "-DLASSI_GRID_SAMPLES=128"]
    elif kind == "dwt2d":
        if small_test:
            flags += ["-DLASSI_DWT_SIDE=32", "-DLASSI_DWT_LEVELS=3"]
    else:
        raise ValueError(f"Unknown native workload: {kind}")
    run([cc, "-std=c11", *sources, *flags, "-lm", "-o", str(output)])
    (directory / "reference-sha256.txt").write_text(
        hashlib.sha256(reference.read_bytes()).hexdigest() + "\n"
    )


def configuration(
    root: Path,
    workload: dict[str, Any],
    dataset: str,
    native_root: Path,
) -> RunConfig:
    """Bind an explicit workload to its C ABI and exact native build command."""
    kind = KINDS[workload["id"]]
    source = root / "benchmarks/checks/native" / (kind + ".c")
    spec = root / "benchmarks/checks" / (kind + ".json")
    expected = workload["correctness"]["reference_sha256"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError(f"Native fixture reference hash mismatch: {source}")
    for item in workload["sources"]:
        original = root / item["path"]
        if hashlib.sha256(original.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Source hash mismatch: {original}")
    build = [
        sys.executable,
        "-m",
        "lassi_x.workload_native",
        kind,
        "--root",
        str(root),
        "--native-root",
        str(native_root),
        "--reference",
        "{reference}",
        "--output",
        "{oracle_dir}/reference",
    ]
    if dataset != "large":
        build.append("--small-test")
    model = {"model": "configure-before-live-use"}
    context = [str(root / item["path"]) for item in workload["sources"]]
    bridge = source.with_name(kind + "-bridge.cpp")
    if bridge.exists():
        context.append(str(bridge))
    for extension in (".c", ".f90"):
        bridge = source.with_name(kind + "-bridge" + extension)
        if bridge.exists():
            context.append(str(bridge))
    return RunConfig.model_validate(
        {
            "version": 1,
            "project": {"root": str(root)},
            "kernel": {
                "name": workload["name"],
                "reference": str(source),
                "context": context,
                "validation_dataset": dataset,
                "task": "Implement the complete declared native computation with the exact "
                "named inputs and every output in fixture order. Every seeded random "
                "case uses the same LARGE dimensions and must pass.",
            },
            "oracle": {
                "fixture_spec": str(spec),
                "build": build,
                "run": ["{oracle_dir}/reference"],
                "timeout_s": 1800,
                "determinism_runs": 2,
            },
            "models": {"planner": model, "compensation": model, "candidates": [model]},
            "arena": {"candidates": 1, "equivalence": {"rtol": 1e-6, "atol": 1e-7}},
            "measure": {
                "evaluation_dataset": dataset,
                "precisions": ["fp64"],
                "backends": [
                    {"type": "torch", "name": "cpu", "device": "cpu", "precisions": ["fp64"]}
                ],
            },
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(KINDS.values()))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--native-root", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--small-test", action="store_true")
    args, extra = parser.parse_known_args()
    compile_reference(
        args.root,
        args.native_root,
        args.kind,
        args.reference,
        args.output,
        small_test=args.small_test,
        extra_flags=extra,
    )


if __name__ == "__main__":
    main()
