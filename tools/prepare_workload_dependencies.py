"""Build the pinned native dependencies for the active workload fixture adapters.

Uses initialized Git submodules and local compilers. No source downloads,
model requests or accelerator execution occur in this preparation step.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

PINS = {
    "third_party/blaspp": "2628ac538fee95417429c846f09f1017c764a2a8",
    "third_party/lapackpp": "047cb8c999866f3b8558de7d5ea2165e108835b5",
    "third_party/random123": "726a093cd9a73f3ec3c8d7a70ff10ed8efec8d13",
    "benchmarks/randlapack/RandBLAS": "c8882c51c6c11e3e2c0c82a311d1de6cc08cb195",
}


def prepare(root: Path, destination: Path, jobs: int) -> None:
    root, destination = root.resolve(), destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((root / "benchmarks/provenance/workloads-39.json").read_text())
    pins = {
        **PINS,
        **{
            v["path"]: v["commit"]
            for k, v in manifest["suites"].items()
            if k in {"itk", "randlapack"}
        },
    }
    for path, expected in pins.items():
        actual = subprocess.check_output(
            ["git", "-C", str(root / path), "rev-parse", "HEAD"], text=True
        ).strip()
        if actual != expected:
            raise ValueError(f"Native dependency pin mismatch: {path}")
        subprocess.run(["git", "-C", str(root / path), "diff", "--quiet", "HEAD"], check=True)
    cmake = shutil.which("cmake")
    if cmake is None or shutil.which("gfortran") is None:
        raise RuntimeError("Install cmake and gfortran before native preparation")
    record: dict[str, Any] = {
        "status": "building",
        "pins": pins,
        "commands": [],
        "platform": platform.platform(),
        "recipe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    report = destination / "dependencies.json"

    def run(command: list[str]) -> None:
        record["commands"].append(command)
        report.write_text(json.dumps(record, indent=2) + "\n")
        subprocess.run(command, check=True, timeout=1800)

    def build(
        source: Path, directory: Path, prefix: Path, flags: list[str], install: bool = True
    ) -> None:
        run(
            [
                cmake,
                "-S",
                str(source),
                "-B",
                str(directory),
                "-DCMAKE_BUILD_TYPE=Release",
                f"-DCMAKE_INSTALL_PREFIX={prefix}",
                *flags,
            ]
        )
        command = [cmake, "--build", str(directory), "--parallel", str(jobs)]
        if install:
            command += ["--target", "install"]
        run(command)

    # Minimal ITK module closure, retaining the original ITK histogram implementation.
    build(
        root / "benchmarks/itk",
        destination / "itk-build",
        destination / "itk-install",
        [
            "-DBUILD_TESTING=OFF",
            "-DBUILD_EXAMPLES=OFF",
            "-DITK_BUILD_DEFAULT_MODULES=OFF",
            "-DModule_ITKStatistics=ON",
            "-DModule_ITKImageCompose=ON",
            "-DModule_ITKImageIntensity=ON",
            "-DBUILD_SHARED_LIBS=OFF",
        ],
        install=False,
    )
    build_root = destination / "randnla/build"
    install_root = destination / "randnla/install"
    blas_prefix, lapack_prefix = install_root / "blaspp", install_root / "lapackpp"
    common = [
        "-Dbuild_tests=OFF",
        "-Duse_openmp=OFF",
        "-Dgpu_backend=none",
        "-DBUILD_SHARED_LIBS=OFF",
    ]
    build(
        root / "third_party/blaspp",
        build_root / "blaspp",
        blas_prefix,
        [
            *common,
            "-Dblas_int=int32",
            "-Dblas=apple" if platform.system() == "Darwin" else "-Dblas=openblas",
        ],
    )
    build(
        root / "third_party/lapackpp",
        build_root / "lapackpp",
        lapack_prefix,
        [*common, f"-Dblaspp_DIR={blas_prefix / 'lib/cmake/blaspp'}"],
    )
    build(
        root / "benchmarks/randlapack",
        build_root / "RandLAPACK",
        install_root / "RandLAPACK-install",
        [
            "-DRandLAPACK_BUILD_TESTS=OFF",
            "-DBUILD_TESTS=OFF",
            "-DBUILD_SHARED_LIBS=OFF",
            "-DCMAKE_DISABLE_FIND_PACKAGE_OpenMP=TRUE",
            f"-Dblaspp_DIR={blas_prefix / 'lib/cmake/blaspp'}",
            f"-Dlapackpp_DIR={lapack_prefix / 'lib/cmake/lapackpp'}",
            f"-DRandom123_DIR={root / 'third_party/random123/include'}",
        ],
    )
    record["libraries"] = {
        str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
        for parent in (destination / "itk-build/lib", install_root)
        for path in parent.rglob("*")
        if path.is_file() and path.suffix in {".a", ".so", ".dylib"}
    }
    record["status"] = "complete"
    report.write_text(json.dumps(record, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--jobs", type=int, default=4, choices=range(1, 17))
    args = parser.parse_args()
    prepare(args.root, args.destination, args.jobs)


if __name__ == "__main__":
    main()
