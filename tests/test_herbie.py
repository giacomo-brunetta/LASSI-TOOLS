from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import torch

from lassi_x.herbie import (
    UnsupportedExpressionError,
    extract,
    fpcore,
    generate,
    optimize,
    parse,
    prepare,
)

SOURCE = """import torch

class Formula(torch.nn.Module):
    def forward(self, x, y):
        a = x * y
        return torch.sqrt(a + 1.0)

def make_model():
    return Formula()
"""
DOMAINS = {"x": (0.1, 2.0), "y": (0.2, 3.0)}


def model(source: str) -> Any:
    namespace: dict[str, Any] = {}
    exec(compile(source, "test-formula", "exec"), namespace)
    return namespace["make_model"]()


def prepared(tmp_path: Path, precision: str = "binary32") -> Path:
    source = tmp_path / "formula.py"
    source.write_text(SOURCE)
    output = tmp_path / "prepared"
    prepare(source, output, class_name="Formula", domains=DOMAINS, precision=precision)
    return output


def test_static_preparation_is_reproducible_and_never_imports_source(tmp_path: Path) -> None:
    source = tmp_path / "formula.py"
    # Importing this would raise. Preparation must be entirely static.
    source.write_text(SOURCE + '\nraise RuntimeError("must not import")\n')
    a, b = tmp_path / "a", tmp_path / "b"
    for output in (a, b):
        prepare(source, output, class_name="Formula", domains=DOMAINS)
    assert {p.name: p.read_bytes() for p in a.iterdir()} == {
        p.name: p.read_bytes() for p in b.iterdir()
    }
    assert json.loads((a / "manifest.json").read_text())["validated"] is False
    with pytest.raises(FileExistsError):
        prepare(source, a, class_name="Formula", domains=DOMAINS)


@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16, torch.float32, torch.float64])
def test_roundtrip_preserves_broadcasting_and_other_dtype_controls(dtype: torch.dtype) -> None:
    program = extract(SOURCE, "Formula")
    core = fpcore(program, DOMAINS)
    generated = generate(program, core)
    assert generated == generate(program, core)
    x = torch.linspace(0.1, 2.0, 21, dtype=dtype).reshape(3, 7)
    y = torch.linspace(0.2, 3.0, 7, dtype=dtype)
    torch.testing.assert_close(model(generated)(x, y), model(SOURCE)(x, y), rtol=0, atol=0)


def test_eliminated_arguments_and_constant_result_keep_broadcast_shape() -> None:
    source = SOURCE.replace("a = x * y\n        return torch.sqrt(a + 1.0)", "return x + y - x - y")
    program = extract(source, "Formula")
    result = generate(program, "(FPCore (arg0 arg1) :precision binary32 0.0)")
    value = model(result)(torch.ones(3, 1), torch.ones(1, 5))
    assert value.shape == (3, 5)
    assert value.dtype == torch.float32
    assert torch.count_nonzero(value) == 0


def test_explicit_cast_does_not_move_its_operand_arithmetic_to_wider_precision() -> None:
    source = SOURCE.replace(
        "a = x * y\n        return torch.sqrt(a + 1.0)",
        "a = (x + y).to(torch.float64)\n        return (a * a).to(torch.float32)",
    )
    program = extract(source, "Formula")
    core = fpcore(program, DOMAINS)
    assert "(cast (! :precision binary32 (+ arg0 arg1)))" in core
    candidate = model(generate(program, core))
    x, y = torch.tensor([2**24], dtype=torch.float32), torch.tensor([1.0])
    torch.testing.assert_close(candidate(x, y), model(source)(x, y), rtol=0, atol=0)


def test_let_and_let_star_have_distinct_scopes() -> None:
    program = extract(SOURCE, "Formula")
    body = "(let ((v arg0)) (let ((v arg1) (w v)) (- v w)))"
    result = model(generate(program, f"(FPCore (arg0 arg1) :precision binary32 {body})"))
    assert result(torch.tensor([2.0]), torch.tensor([5.0])).item() == 3
    body = body.replace("(let ((v arg1)", "(let* ((v arg1)")
    result = model(generate(program, f"(FPCore (arg0 arg1) :precision binary32 {body})"))
    assert result(torch.tensor([2.0]), torch.tensor([5.0])).item() == 0


@pytest.mark.parametrize(
    "body",
    [
        "return x.sum() + y",
        "return x @ y",
        "x += y\n        return x",
        "return torch.add(x, y, alpha=2)",
        "return self.weight * x + y",
        "return torch.where(x > 0, x, y)",
        "for i in range(3):\n            x = x + y\n        return x",
        "return x",
        "return x + y.to(torch.float64)",
        "return x + (0.1 + 0.2) + y",
    ],
)
def test_unsupported_source_fails_before_creating_artifacts(tmp_path: Path, body: str) -> None:
    source = tmp_path / "source.py"
    source.write_text(SOURCE.replace("a = x * y\n        return torch.sqrt(a + 1.0)", body))
    with pytest.raises(UnsupportedExpressionError):
        prepare(source, tmp_path / "out", class_name="Formula", domains=DOMAINS)
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("precision", ["binary16", "bfloat16"])
def test_low_precision_requires_a_custom_platform(tmp_path: Path, precision: str) -> None:
    with pytest.raises(ValueError, match="custom Herbie platform"):
        prepared(tmp_path, precision)
    assert not (tmp_path / "prepared").exists()
    extract(SOURCE, "Formula", precision)
    with pytest.raises(UnsupportedExpressionError, match="exactly representable"):
        extract(SOURCE.replace("1.0", "0.1"), "Formula", precision)


@pytest.mark.parametrize(
    "core",
    [
        "(FPCore (arg0 arg1) :precision binary32 (fma arg0 arg1 1.0))",
        "(FPCore (arg0 arg1) :precision binary32 (if (< arg0 0) arg0 arg1))",
        "(FPCore (arg0 arg1) :precision binary64 arg0)",
        "(FPCore (x y) :precision binary32 x)",
        "(FPCore (arg0 arg1) :precision binary32 INFINITY)",
        "(FPCore (arg0 arg1) :precision binary32 (__import__ os))",
        "(FPCore (arg0 arg1) :precision binary32 (! :precision (binary32) arg0))",
        "(FPCore (arg0 arg1) :precision binary32 arg0) (FPCore (x) x)",
        "(FPCore (arg0 arg1) :precision binary32 arg0]",
    ],
)
def test_unknown_or_malformed_output_is_refused(core: str) -> None:
    with pytest.raises(UnsupportedExpressionError):
        generate(extract(SOURCE, "Formula"), core)


def fake_tool(tmp_path: Path, body: str) -> list[str]:
    script = tmp_path / "tool.py"
    script.write_text("import sys\nfrom pathlib import Path\n" + body)
    return [sys.executable, str(script)]


def test_execution_records_unvalidated_proposal_and_never_overwrites(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    command = fake_tool(
        tmp_path, "Path(sys.argv[-1]).write_bytes(Path(sys.argv[-2]).read_bytes())\n"
    )
    proposal = optimize(output, command=command)
    record = json.loads((output / "manifest.json").read_text())
    assert record["status"] == "proposal" and record["validated"] is False
    assert proposal.exists() and (output / "stderr.log").exists()
    with pytest.raises(ValueError, match="exactly one"):
        optimize(output, command=command)


def test_failed_execution_retains_evidence_without_a_proposal(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    command = fake_tool(tmp_path, 'print("diagnostic", file=sys.stderr)\nsys.exit(7)\n')
    with pytest.raises(RuntimeError, match="status 7"):
        optimize(output, command=command)
    record = json.loads((output / "manifest.json").read_text())
    assert record["status"] == "failed" and record["returncode"] == 7
    assert (output / "stderr.log").read_text() == "diagnostic\n"
    assert not (output / "proposal.py").exists()


def test_timeout_is_a_failure_and_process_is_reaped(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    command = fake_tool(tmp_path, "import time\ntime.sleep(30)\n")
    with pytest.raises(subprocess.TimeoutExpired):
        optimize(output, command=command, timeout_s=0.15)
    assert json.loads((output / "manifest.json").read_text())["failure_type"] == "TimeoutExpired"
    assert not (output / "proposal.py").exists()


def test_execution_detects_tampering_before_launch(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    (output / "original.py").write_text(SOURCE + "\n")
    with pytest.raises(ValueError, match="changed"):
        optimize(output, command=["does-not-exist"])
    assert not (output / "stdout.log").exists()


def test_execution_rejects_narrowed_domains(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    command = fake_tool(
        tmp_path,
        'Path(sys.argv[-1]).write_text("(FPCore (arg0 arg1) :precision binary32 0.0)")\n',
    )
    with pytest.raises(UnsupportedExpressionError, match="input domain"):
        optimize(output, command=command)
    assert not (output / "proposal.py").exists()


@pytest.mark.parametrize(
    "marker", ["Crash in example", "Error in example", "example times out in 60s"]
)
def test_zero_exit_with_herbie_failure_marker_is_not_a_proposal(
    tmp_path: Path, marker: str
) -> None:
    output = prepared(tmp_path)
    command = fake_tool(
        tmp_path,
        f"Path(sys.argv[-1]).write_text(';; {marker}\\n' + Path(sys.argv[-2]).read_text())\n",
    )
    with pytest.raises(RuntimeError, match="unsuccessful job"):
        optimize(output, command=command)
    assert json.loads((output / "manifest.json").read_text())["status"] == "failed"
    assert not (output / "proposal.py").exists()


def test_custom_platform_is_snapshotted_and_verified(tmp_path: Path) -> None:
    source = tmp_path / "source.py"
    source.write_text(SOURCE)
    platform = tmp_path / "custom.rkt"
    platform.write_text("#lang herbie/platform\n")
    output = tmp_path / "out"
    prepare(source, output, class_name="Formula", domains=DOMAINS, platform=platform)
    assert (output / "platform.rkt").read_bytes() == platform.read_bytes()
    (output / "platform.rkt").write_text("changed")
    with pytest.raises(ValueError, match="platform changed"):
        optimize(output, command=["does-not-exist"])


def test_comments_and_brackets_are_read_as_data() -> None:
    assert parse("; comment\n(let ([x 1]) x)") == [["let", [["x", "1"]], "x"]]


def test_domain_normalization_accepts_equivalent_chained_bounds(tmp_path: Path) -> None:
    output = prepared(tmp_path)
    command = fake_tool(
        tmp_path,
        "text = Path(sys.argv[-2]).read_text()\n"
        'text = text.replace("(<= 0.1 arg0 2.0)", "(and (<= 1/10 arg0) (<= arg0 2))")\n'
        "Path(sys.argv[-1]).write_text(text)\n",
    )
    assert optimize(output, command=command).exists()


def test_argument_names_do_not_shadow_generated_guard_builtins() -> None:
    source = SOURCE.replace("x", "all").replace("y", "isinstance")
    program = extract(source, "Formula")
    candidate = model(
        generate(program, fpcore(program, {"all": (1.0, 2.0), "isinstance": (1.0, 2.0)}))
    )
    torch.testing.assert_close(
        candidate(torch.ones(3), torch.ones(3)), torch.full((3,), 2.0).sqrt()
    )


def test_optional_native_fp16_rounding_and_roundtrip(tmp_path: Path) -> None:
    racket = os.environ.get("LASSI_HERBIE_RACKET")
    if racket is None:
        pytest.skip("Set LASSI_HERBIE_RACKET and PLTUSERHOME for the isolated native test")
    platform = Path(__file__).resolve().parents[1] / "lassi_x/resources/herbie-fp16.rkt"
    generator = torch.Generator().manual_seed(817)
    values = torch.randn(2048, dtype=torch.float64, generator=generator) * 40000
    # Every finite half value and every adjacent positive midpoint, including
    # subnormal transitions, ties-to-even, signed zero, and overflow neighbors.
    positives = torch.arange(0x7C00, dtype=torch.int16).view(torch.float16).to(torch.float64)
    midpoints = (positives[:-1] + positives[1:]) / 2
    values = torch.cat(
        [
            values,
            positives,
            -positives,
            midpoints,
            -midpoints,
            torch.tensor([65519.0, 65520.0, 65521.0, -0.0], dtype=torch.float64),
        ]
    )
    inputs = tmp_path / "rounding-inputs.json"
    # Racket's JSON number reader normalizes -0.0; read numeric strings to
    # preserve signed zero in the transport being used to test the quantizer.
    inputs.write_text(json.dumps([repr(v) for v in values.tolist()]))
    script = tmp_path / "check.rkt"
    script.write_text("""#lang racket
(require json)
(define arguments (current-command-line-arguments))
(define platform (string->path (vector-ref arguments 0)))
(define half-round (dynamic-require platform 'half-round))
(define encode (dynamic-require platform 'half->ordinal))
(define decode (dynamic-require platform 'ordinal->half))
(define mismatches
  (for/sum ([i (in-range (- #x7bff) (add1 #x7bff))])
    (if (= i (encode (decode i))) 0 1)))
(define values (map string->number (call-with-input-file (vector-ref arguments 1) read-json)))
(write-json (hash 'mismatches mismatches
                  'rounded (map (lambda (x) (number->string (half-round x))) values)))
""")
    result = subprocess.run(
        [racket, str(script), str(platform), str(inputs)],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    report = json.loads(result.stdout)
    assert report["mismatches"] == 0
    actual = torch.tensor(
        [float(v.replace("+inf.0", "inf").replace("-inf.0", "-inf")) for v in report["rounded"]],
        dtype=torch.float64,
    )
    expected = values.to(torch.float16).to(torch.float64)
    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
    assert torch.equal(torch.signbit(actual), torch.signbit(expected))
    source = tmp_path / "difference.py"
    source.write_text(
        SOURCE.replace(
            "a = x * y\n        return torch.sqrt(a + 1.0)", "return (x*x - y*y) / (x-y)"
        )
    )
    output = tmp_path / "native"
    prepare(
        source,
        output,
        class_name="Formula",
        domains={"x": (100.0, 120.0), "y": (90.0, 99.0)},
        precision="binary16",
        platform=platform,
    )
    proposal = optimize(output, command=[racket, "-l", "herbie"], timeout_s=60)
    x = torch.linspace(100, 120, 101, dtype=torch.float16).reshape(-1, 1)
    y = torch.linspace(90, 99, 101, dtype=torch.float16).reshape(1, -1)
    expected = x.to(torch.float64) + y.to(torch.float64)
    base = model(source.read_text())(x, y)
    candidate = model(proposal.read_text())(x, y)
    assert (candidate - expected).abs().max() < (base - expected).abs().max()
