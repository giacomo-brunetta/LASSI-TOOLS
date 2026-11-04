from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from lassi_x.tenspiler_prepare import UnsupportedSourceError, prepare

CLANG = shutil.which("clang")
pytestmark = pytest.mark.skipif(CLANG is None, reason="Clang AST frontend unavailable")
ROOT = Path(__file__).resolve().parents[1]
GENERIC = """
void compute(int height, int width, double table[3][4], double values[4], double result[3]) {
    int row, col;
    for (row=0; row<height; row++) {
        result[row]=0;
        for (col=0; col<width; col++) result[row] += table[row][col]*values[col];
    }
}
"""


def source(tmp_path: Path, code: str = GENERIC) -> Path:
    path = tmp_path / "input.c"
    path.write_text(code)
    return path


def test_generic_ast_conversion_is_reproducible_and_preserves_source(tmp_path: Path) -> None:
    original = source(tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    manifest = prepare(original, a, function="compute", integer_model=True)
    prepare(original, b, function="compute", integer_model=True)
    assert original.read_text() == GENERIC
    assert {p.name: p.read_bytes() for p in a.iterdir()} == {
        p.name: p.read_bytes() for p in b.iterdir()
    }
    assert manifest["program"]["inputs"] == ("table", "values")
    assert manifest["program"]["outputs"] == ("result",)
    assert manifest["program"]["stages"][0]["transpose"] is False
    assert "double curr" in (a / "stage_result.reference.cc").read_text()
    assert "int curr" in (a / "stage_result.cc").read_text()
    assert manifest["floating_point_equivalence_proven"] is False
    assert str(original.resolve()) in manifest["dependencies"]
    with pytest.raises(FileExistsError):
        prepare(original, a, function="compute")


def test_floating_input_does_not_silently_become_integer(tmp_path: Path) -> None:
    out = tmp_path / "out"
    prepare(source(tmp_path), out, function="compute")
    assert not (out / "stage_result.cc").exists()
    assert not (out / "synthesize.py").exists()
    assert json.loads((out / "manifest.json").read_text())["integer_model"] is False


@pytest.mark.parametrize(
    "code",
    [
        GENERIC.replace("row=0", "row=1"),
        GENERIC.replace("row++", "row+=2"),
        GENERIC.replace("row<height", "row<=height"),
        GENERIC.replace("result[row]=0;", "result[row]=1;"),
        GENERIC.replace("result[row] +=", "if (values[col]>0) result[row] +="),
        GENERIC.replace("table[row][col]*values[col]", "table[row][col]/values[col]"),
        GENERIC.replace("table[row][col]*values[col]", "table[row][col]*values[row]"),
        GENERIC.replace("double values[4], ", "").replace("values[col]", "result[col]"),
        GENERIC.replace("result[row]=0;", "result[row]=0; result[row]=0;"),
        GENERIC.replace("int row, col;", "int row, col; int unused=1;"),
        GENERIC.replace("row<height", "row<width-1"),
        GENERIC.replace("values", "lambda"),
        GENERIC.replace("values", "stage_result_torch"),
        GENERIC.replace("height", "size_t"),
    ],
)
def test_unsupported_source_is_refused_without_partial_output(tmp_path: Path, code: str) -> None:
    output = tmp_path / "out"
    with pytest.raises(UnsupportedSourceError):
        prepare(source(tmp_path, code), output, function="compute", integer_model=True)
    assert not output.exists()


def test_partial_intermediate_is_rejected(tmp_path: Path) -> None:
    code = """
void compute(int n, double A[4][4], double x[4], double t[4], double y[4]) {
 int i,j;
 for(i=0;i<n;i++) y[i]=0;
 for(i=0;i<n;i++) {
  t[i]=0;
  for(j=0;j<n;j++) {
   t[i] += A[i][j]*x[j];
   y[j] += A[i][j]*t[i];
  }
 }
}
"""
    with pytest.raises(UnsupportedSourceError, match="before it is complete"):
        prepare(source(tmp_path, code), tmp_path / "out", function="compute")


def test_generated_cpp_matches_independent_original_c(tmp_path: Path) -> None:
    if not shutil.which("clang++"):
        pytest.skip("C++ compiler unavailable")
    original = source(tmp_path)
    out = tmp_path / "out"
    prepare(original, out, function="compute")
    c_harness = tmp_path / "reference.c"
    c_harness.write_text(
        '#include <stdio.h>\n#include "input.c"\n'
        "int main(void) { double a[3][4]={{1,-2,3,4},{5,0,2,-1},{3,2,-4,1}};"
        "double x[4]={0.5,-0.25,2,3}, y[3]; compute(3,4,a,x,y);"
        'for(int i=0;i<3;i++) printf("%.17g\\n",y[i]); }\n'
    )
    cpp_harness = out / "check.cc"
    cpp_harness.write_text(
        '#include <cstdio>\n#include "kernel.reference.cc"\n'
        "int main() { auto y=compute_adapted(3,4,{{1,-2,3,4},{5,0,2,-1},{3,2,-4,1}},"
        "{0.5,-0.25,2,3});"
        'for(auto v:y[0]) std::printf("%.17g\\n",v); }\n'
    )
    for compiler, src, exe in [
        ("clang", c_harness, tmp_path / "ref"),
        ("clang++", cpp_harness, tmp_path / "adapted"),
    ]:
        subprocess.run(
            [compiler, "-O0", "-ffp-contract=off", str(src), "-o", str(exe)],
            check=True,
            capture_output=True,
            timeout=30,
        )
    assert subprocess.check_output([str(tmp_path / "ref")]) == subprocess.check_output(
        [str(tmp_path / "adapted")]
    )


@pytest.mark.parametrize("kernel", ["atax", "bicg"])
def test_polybench_structures_not_kernel_names(tmp_path: Path, kernel: str) -> None:
    base = ROOT / "benchmarks/polybench"
    original = base / f"linear-algebra/kernels/{kernel}/{kernel}.c"
    if not original.exists():
        pytest.skip("PolyBench submodule uninitialized")
    renamed = tmp_path / f"{kernel}.c"
    renamed.write_text(original.read_text().replace(f"kernel_{kernel}", "different_name"))
    shutil.copyfile(original.with_suffix(".h"), tmp_path / f"{kernel}.h")
    manifest = prepare(
        renamed,
        tmp_path / "out",
        function="different_name",
        includes=(base / "utilities",),
        defines=("MINI_DATASET",),
        integer_model=True,
    )
    program = manifest["program"]
    assert program["function"] == "different_name"
    assert len(program["stages"]) == 2
    assert {s["transpose"] for s in program["stages"]} == {True, False}


def test_generated_runner_rejects_changed_input(tmp_path: Path) -> None:
    out = tmp_path / "out"
    prepare(source(tmp_path), out, function="compute", integer_model=True)
    (out / "stage_result.cc").write_text("modified")
    process = subprocess.run(
        [
            "python3",
            str(out / "synthesize.py"),
            "--tenspiler-root",
            str(tmp_path),
            "--llvm-bin",
            str(tmp_path),
            "--llvm-pass",
            str(tmp_path / "pass.so"),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode != 0
    assert "Prepared file changed" in process.stderr
    assert not (out / "synthesis").exists()


def test_nonzero_accumulator_is_an_explicit_input(tmp_path: Path) -> None:
    code = GENERIC.replace("result[row]=0;", "")
    out = tmp_path / "out"
    manifest = prepare(source(tmp_path, code), out, function="compute", integer_model=True)
    assert "result" in manifest["program"]["inputs"]
    assert manifest["program"]["stages"][0]["bias"] is True
    assert "curr = bias[row]" in (out / "stage_result.reference.cc").read_text()


def test_mvt_is_not_rejected_for_its_input_accumulators(tmp_path: Path) -> None:
    base = ROOT / "benchmarks/polybench"
    original = base / "linear-algebra/kernels/mvt/mvt.c"
    if not original.exists():
        pytest.skip("PolyBench submodule uninitialized")
    manifest = prepare(
        original,
        tmp_path / "out",
        includes=(base / "utilities",),
        defines=("MINI_DATASET",),
        integer_model=True,
    )
    assert manifest["program"]["inputs"] == ("x1", "x2", "y_1", "y_2", "A")
    assert all(s["bias"] for s in manifest["program"]["stages"])
