from __future__ import annotations

import importlib.util
import shutil
import subprocess
from fractions import Fraction
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import numpy as np
import pytest
import torch

from lassi_x.tenspiler_affine import affine, same_iteration
from lassi_x.tenspiler_prepare import prepare

pytestmark = pytest.mark.skipif(shutil.which("clang") is None, reason="Clang unavailable")


def runtime(manifest: dict[str, Any], folder: Path) -> Any:
    spec = importlib.util.spec_from_file_location("affine_runtime_test", folder / "runtime.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Semantic unit tests of orchestration. Actual Tenspiler operator generation
    # is exercised separately by the frozen native campaigns.
    ops = {
        "add": lambda a, b: a + b,
        "sub": lambda a, b: a - b,
        "mul": lambda a, b: a * b,
        "div": lambda a, b: a / b,
        "sum": torch.sum,
        "max": torch.max,
        "mv": torch.matmul,
        "sqrt": lambda a: torch.sqrt(torch.as_tensor(a)),
        "exp": lambda a: torch.exp(torch.as_tensor(a)),
        "select": lambda c, a, b: torch.where(
            torch.as_tensor(c) != 0, torch.as_tensor(a), torch.as_tensor(b)
        ),
    }
    return module.build(manifest["program"], ops)


def test_matrix_reduction_matches_executed_original_c(tmp_path: Path) -> None:
    original = tmp_path / "matrix.c"
    code = """
#include <stdio.h>
void kernel_matrix(int m,int n,int k,double alpha,double beta,
 double C[2][3],double A[2][4],double B[4][3]) {
 int i,j,q;
 for(i=0;i<m;i++) {
  for(j=0;j<n;j++) C[i][j]*=beta;
  for(q=0;q<k;q++) for(j=0;j<n;j++) C[i][j]+=alpha*A[i][q]*B[q][j];
 }
}
int main(void) {
 double A[2][4],B[4][3],C[2][3];
 for(int i=0;i<2;i++) for(int j=0;j<4;j++) A[i][j]=(i-j)*0.125;
 for(int i=0;i<4;i++) for(int j=0;j<3;j++) B[i][j]=(2*i+j-3)*0.25;
 for(int i=0;i<2;i++) for(int j=0;j<3;j++) C[i][j]=(i+j+1)*0.5;
 fwrite(A,sizeof(double),8,stdout); fwrite(B,sizeof(double),12,stdout);
 fwrite(C,sizeof(double),6,stdout);
 kernel_matrix(2,3,4,1.5,-0.5,C,A,B);
 fwrite(C,sizeof(double),6,stdout);
}
"""
    original.write_text(code)
    out = tmp_path / "prepared"
    manifest = prepare(original, out, integer_model=True, extended=True)
    assert manifest["schema_version"] == 2
    subprocess.run(
        ["clang", "-O0", "-ffp-contract=off", str(original), "-o", str(tmp_path / "ref")],
        check=True,
        capture_output=True,
        timeout=30,
    )
    values = np.frombuffer(
        subprocess.check_output([str(tmp_path / "ref")]), dtype=np.float64
    ).copy()
    a = torch.tensor(values[:8].reshape(2, 4))
    b = torch.tensor(values[8:20].reshape(4, 3))
    c = torch.tensor(values[20:26].reshape(2, 3))
    snapshot = c.clone()
    actual = runtime(manifest, out)(2, 3, 4, 1.5, -0.5, c, a, b)[0]
    torch.testing.assert_close(
        actual, torch.tensor(values[26:].reshape(2, 3)), rtol=1e-13, atol=1e-13
    )
    assert torch.equal(c, snapshot)


def test_in_place_stencil_is_not_parallelized(tmp_path: Path) -> None:
    source = tmp_path / "recurrence.c"
    source.write_text("""
void kernel_recur(int n,double a[5]) { int i;
for(i=1;i<n;i++) a[i]=a[i-1]+a[i]; }
""")
    out = tmp_path / "out"
    manifest = prepare(source, out, integer_model=True, extended=True)
    loop = manifest["program"]["body"]["statements"][1]
    assert loop["parallel"] is False
    tensor = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0], dtype=torch.float64)
    actual = runtime(manifest, out)(5, tensor)[0]
    torch.testing.assert_close(
        actual, torch.tensor([1.0, 3.0, 6.0, 10.0, 15.0], dtype=torch.float64)
    )
    assert torch.equal(tensor, torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0], dtype=torch.float64))


def test_fractional_literal_is_not_truncated_in_composition(tmp_path: Path) -> None:
    source = tmp_path / "stencil.c"
    source.write_text("""
void kernel_map(int n,double a[5],double b[5]) { int i;
for(i=1;i<n-1;i++) b[i]=0.25*(a[i-1]+a[i]+a[i+1]); }
""")
    out = tmp_path / "out"
    manifest = prepare(source, out, integer_model=True, extended=True)
    loop = manifest["program"]["body"]["statements"][1]
    assert loop["parallel"] is True
    a = torch.tensor([1.0, 2.0, 3.0, 4.0, 5.0], dtype=torch.float64)
    b = torch.tensor([7.0, 0.0, 0.0, 0.0, 9.0], dtype=torch.float64)
    actual = runtime(manifest, out)(5, a, b)[0]
    torch.testing.assert_close(
        actual, torch.tensor([7.0, 1.5, 2.25, 3.0, 9.0], dtype=torch.float64)
    )


def test_affine_overlap_requires_same_iteration() -> None:
    def var(name: str) -> dict[str, Any]:
        return {"kind": "var", "name": name}

    def access(a: str, b: str) -> dict[str, Any]:
        return {"kind": "array", "name": "A", "indices": [var(a), var(b)]}

    assert same_iteration(access("i", "j"), access("j", "i"), "j", set())
    shifted: dict[str, Any] = {
        "kind": "array",
        "name": "A",
        "indices": [
            var("i"),
            {
                "kind": "binary",
                "op": "-",
                "left": var("j"),
                "right": {"kind": "literal", "value": 1},
            },
        ],
    }
    assert not same_iteration(access("i", "j"), shifted, "j", set())
    assert affine(shifted["indices"][1]) == {"j": Fraction(1), "": Fraction(-1)}


@pytest.mark.parametrize("negative", [False, True])
def test_guarded_pivot_matches_c_including_fallback(tmp_path: Path, negative: bool) -> None:
    source = tmp_path / "paths.c"
    diagonal = -1 if negative else 0
    source.write_text(
        """
#include <stdio.h>
void kernel_paths(int n,int d[3][3]) { int i,j,k;
 for(k=0;k<n;k++) { for(i=0;i<n;i++) for(j=0;j<n;j++)
 d[i][j]=d[i][j]<d[i][k]+d[k][j]?d[i][j]:d[i][k]+d[k][j]; }
}
int main(void) { int d[3][3]={{DIAG,3,8},{4,0,2},{1,7,0}};
 fwrite(d,sizeof(int),9,stdout); kernel_paths(3,d); fwrite(d,sizeof(int),9,stdout); }
""".replace("DIAG", str(diagonal))
    )
    out = tmp_path / "out"
    manifest = prepare(source, out, integer_model=True, extended=True)
    assert manifest["program"]["body"]["statements"][1]["kind"] == "pivot-min-plus"
    subprocess.run(
        ["clang", str(source), "-o", str(tmp_path / "ref")],
        check=True,
        capture_output=True,
        timeout=30,
    )
    data = np.frombuffer(subprocess.check_output([str(tmp_path / "ref")]), dtype=np.int32).copy()
    actual = runtime(manifest, out)(3, torch.tensor(data[:9].reshape(3, 3)))[0]
    assert np.array_equal(actual.numpy(), data[9:].reshape(3, 3))


def test_wavefront_preserves_inplace_stencil_order(tmp_path: Path) -> None:
    source = tmp_path / "wave.c"
    source.write_text("""
#include <stdio.h>
void kernel_wave(int steps,int n,double a[6][6]) { int t,i,j;
 for(t=0;t<steps;t++) for(i=1;i<n-1;i++) for(j=1;j<n-1;j++)
 a[i][j]=(a[i-1][j-1]+a[i-1][j]+a[i-1][j+1]+a[i][j-1]+a[i][j]+a[i][j+1]+a[i+1][j-1]+a[i+1][j]+a[i+1][j+1])/9.0;
}
int main(void) { double a[6][6];
 for(int i=0;i<6;i++) for(int j=0;j<6;j++) a[i][j]=(i*5+j+1)*0.125;
 fwrite(a,sizeof(double),36,stdout); kernel_wave(2,6,a); fwrite(a,sizeof(double),36,stdout); }
""")
    out = tmp_path / "out"
    manifest = prepare(source, out, integer_model=True, extended=True)
    subprocess.run(
        ["clang", "-O0", "-ffp-contract=off", str(source), "-o", str(tmp_path / "ref")],
        check=True,
        capture_output=True,
        timeout=30,
    )
    data = np.frombuffer(subprocess.check_output([str(tmp_path / "ref")]), dtype=np.float64).copy()
    actual = runtime(manifest, out)(2, 6, torch.tensor(data[:36].reshape(6, 6)))[0]
    torch.testing.assert_close(actual, torch.tensor(data[36:].reshape(6, 6)), rtol=0, atol=0)


def test_ordered_reduction_matches_c_cancellation(tmp_path: Path) -> None:
    source = tmp_path / "ordered.c"
    source.write_text("""
#include <stdio.h>
void kernel_order(int n,double a[5],double out[1]) { int i;
 out[0]=0; for(i=0;i<n;i++) out[0]+=a[i]; }
int main(void) { double a[5]={1e16,1,-1e16,3,0.5},out[1];
 fwrite(a,sizeof(double),5,stdout); kernel_order(5,a,out);
 fwrite(out,sizeof(double),1,stdout); }
""")
    out = tmp_path / "prepared"
    manifest = prepare(source, out, integer_model=True, extended=True, ordered_reductions=True)
    assert "mv" not in manifest["program"]["operators"]
    subprocess.run(
        ["clang", "-O3", "-ffp-contract=off", str(source), "-o", str(tmp_path / "ref")],
        check=True,
        capture_output=True,
        timeout=30,
    )
    data = np.frombuffer(subprocess.check_output([str(tmp_path / "ref")]), dtype=np.float64).copy()
    actual = runtime(manifest, out)(5, torch.tensor(data[:5]), torch.zeros(1, dtype=torch.float64))[
        0
    ]
    torch.testing.assert_close(actual, torch.tensor(data[5:]), rtol=0, atol=0)


def test_residual_recurrence_honors_finite_budget(tmp_path: Path) -> None:
    source = tmp_path / "limited.c"
    source.write_text(
        "void kernel_limited(int n,double a[5]) { int i; for(i=1;i<n;i++) a[i]=a[i-1]+a[i]; }"
    )
    out = tmp_path / "prepared"
    manifest = prepare(source, out, integer_model=True, extended=True, scalar_step_limit=2)
    with pytest.raises(RuntimeError, match="scalar-step budget"):
        runtime(manifest, out)(5, torch.ones(5))
