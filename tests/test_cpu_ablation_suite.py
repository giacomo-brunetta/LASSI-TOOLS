from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
import yaml

from lassi_x.config import RunConfig
from lassi_x.validation import build_oracle

if TYPE_CHECKING:
    from numpy.typing import NDArray

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "examples/cpu-ablation-suite/suite.py"
ORDERED_SCRIPT = REPO / "examples/cpu-ablation-suite/run_ordered.py"
SCIENCE = SCRIPT.parent / "scientific"


def cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def ordered_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ORDERED_SCRIPT), *args], capture_output=True, text=True, check=False
    )


@pytest.fixture
def campaign(tmp_path: Path) -> Path:
    polybench = REPO.parent / "PolyBenchC-4.2.1"
    if not (polybench / "utilities/polybench.c").exists():
        pytest.skip("PolyBench/C 4.2.1 source tree not installed")
    model = {"provider": "custom", "model": "test-model"}
    models = tmp_path / "models.yaml"
    models.write_text(
        yaml.safe_dump({"planner": model, "candidates": [model] * 3, "compensation": model})
    )
    output = tmp_path / "campaign"
    result = cli(
        "prepare", "--models-config", str(models), "--output", str(output), "--full-polybench"
    )
    assert result.returncode == 0, result.stderr
    return output


def test_suite_configs_and_preview(campaign: Path) -> None:
    manifest = json.loads((campaign / "suite.json").read_text())
    assert len(manifest["entries"]) == 35
    for entry in manifest["entries"]:
        config = RunConfig.load(campaign / entry["config"])
        assert config.execution.mode == "local"
        assert not config.memory.enabled
        assert not config.compensation.enabled
        assert config.kernel.validation_dataset == config.evaluation_dataset == "mini"
        assert len(config.models.candidates) == config.arena.candidates == 3
        assert all(config.resolve_project_path(p).is_file() for p in config.kernel.context)
    preview = cli("run", str(campaign / "suite.json"))
    assert preview.returncode == 0, preview.stderr
    assert preview.stdout.count("--until cpu-verified") == 35
    assert not (campaign / "runs").exists()
    unknown = cli("run", str(campaign / "suite.json"), "--only", "typo")
    assert unknown.returncode != 0
    assert "Unknown kernels" in unknown.stderr


def test_prepare_configures_scheduler(tmp_path: Path) -> None:
    polybench = REPO.parent / "PolyBenchC-4.2.1"
    if not (polybench / "utilities/polybench.c").exists():
        pytest.skip("PolyBench/C 4.2.1 source tree not installed")
    model = {"provider": "custom", "model": "test-model"}
    models = tmp_path / "models.yaml"
    models.write_text(
        yaml.safe_dump({"planner": model, "candidates": [model], "compensation": model})
    )
    output = tmp_path / "campaign"
    result = cli(
        "prepare",
        "--models-config",
        str(models),
        "--output",
        str(output),
        "--candidates",
        "1",
        "--max-candidate-flows",
        "1",
        "--max-model-sessions",
        "1",
    )
    assert result.returncode == 0, result.stderr
    config = RunConfig.load(output / "configs/polybench-3mm.yaml")
    assert config.scheduler.max_candidate_flows == 1
    assert config.scheduler.max_model_sessions == 1


def test_campaign_rejects_overwrite_and_tampering(campaign: Path) -> None:
    original = (campaign / "suite.json").read_bytes()
    result = cli(
        "prepare",
        "--models-config",
        str(REPO / "examples/polybench-3mm/run.yaml"),
        "--output",
        str(campaign),
    )
    assert result.returncode != 0
    assert (campaign / "suite.json").read_bytes() == original
    config = campaign / "configs/polybench-3mm.yaml"
    config.write_text(config.read_text() + "\n# modified\n")
    result = cli("run", str(campaign / "suite.json"))
    assert result.returncode != 0
    assert "Campaign input changed" in result.stderr


def test_batch_continues_after_failure(campaign: Path, tmp_path: Path) -> None:
    mock_cli = tmp_path / "mock-lassi-x"
    mock_cli.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "assert sys.argv[1] == 'run'\n"
        "assert sys.argv[-2:] == ['--until', 'cpu-verified']\n"
        "print('MOCK-CALL', sys.argv[2])\n"
        "raise SystemExit(1 if 'polybench-3mm.yaml' in sys.argv[2] else 0)\n"
    )
    mock_cli.chmod(0o700)
    result = cli(
        "run",
        str(campaign / "suite.json"),
        "--execute",
        "--lassi-x",
        str(mock_cli),
        "--only",
        "polybench-3mm",
        "direct-dft",
    )
    assert result.returncode == 1
    assert result.stdout.count("MOCK-CALL") == 2
    assert "direct-dft.yaml" in result.stdout


def test_batch_accepts_zero_cooldown(campaign: Path, tmp_path: Path) -> None:
    mock_cli = tmp_path / "mock-lassi-x"
    mock_cli.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "assert sys.argv[1] == 'run'\n"
        "print('MOCK-CALL', sys.argv[2])\n"
    )
    mock_cli.chmod(0o700)
    result = cli(
        "run",
        str(campaign / "suite.json"),
        "--execute",
        "--lassi-x",
        str(mock_cli),
        "--cooldown-s",
        "0",
        "--only",
        "polybench-3mm",
        "direct-dft",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("MOCK-CALL") == 2


def test_ordered_launcher_forwards_cooldown(campaign: Path, tmp_path: Path) -> None:
    result = ordered_cli(
        str(campaign / "suite.json"),
        "--output",
        str(tmp_path / "launcher"),
        "--cooldown-s",
        "90",
        "--only",
        "polybench-3mm",
    )
    assert result.returncode == 0, result.stderr
    assert "--cooldown-s 90" in result.stdout


@pytest.mark.parametrize("candidate_failure", [False, True])
@pytest.mark.parametrize("connection_failure", [False, True])
def test_batch_stops_on_infrastructure_failure(
    campaign: Path, tmp_path: Path, candidate_failure: bool, connection_failure: bool
) -> None:
    mock_cli = tmp_path / "mock-quota-cli"
    error = (
        "RuntimeError: Connection error."
        if connection_failure
        else "RuntimeError: HTTP 429: The usage limit has been reached"
    )
    record = (
        {"candidates": [{"diagnostics": [{"message": error}]}]}
        if candidate_failure
        else {"error": error}
    )
    mock_cli.write_text(
        f"#!{sys.executable}\n"
        "import sys\nfrom pathlib import Path\n"
        "p = Path(sys.argv[2])\n"
        "out = p.parent.parent / 'runs' / p.stem / 'new-attempt'\n"
        "out.mkdir(parents=True)\n"
        f"(out / 'run.json').write_text({json.dumps(record)!r})\n"
        "print('MOCK-CALL')\nraise SystemExit(1)\n"
    )
    mock_cli.chmod(0o700)
    result = cli(
        "run",
        str(campaign / "suite.json"),
        "--execute",
        "--lassi-x",
        str(mock_cli),
        "--only",
        "polybench-3mm",
        "direct-dft",
    )
    assert result.returncode == (3 if connection_failure else 2)
    assert result.stdout.count("MOCK-CALL") == 1
    assert ("connection failed" if connection_failure else "usage limit exhausted") in result.stderr


def test_summary_keeps_failed_attempts(campaign: Path) -> None:
    for name, status in [("attempt-1", "failed"), ("attempt-2", "cpu_verified")]:
        folder = campaign / "runs/polybench-3mm" / name
        folder.mkdir(parents=True)
        (folder / "run.json").write_text(
            json.dumps(
                {
                    "status": status,
                    "candidates": [{"candidate_id": "c1", "model": "test-model", "status": status}],
                }
            )
        )
    result = cli("summary", str(campaign / "suite.json"))
    assert result.returncode == 0
    assert "attempt-1,failed" in result.stdout
    assert "attempt-2,cpu_verified" in result.stdout
    assert "not_run" in result.stdout


def test_all_polybench_and_science_oracles(campaign: Path) -> None:
    if not shutil.which("gcc"):
        pytest.skip("C compiler unavailable")
    result = cli("run", str(campaign / "suite.json"), "--check-oracles")
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("oracle OK") == 35
    # Independently check the scalar mutual-information fixture analytically.
    config = RunConfig.load(campaign / "configs/mutual-information.yaml")
    oracle = asyncio.run(build_oracle(config, campaign / "mi-independent"))
    n = 32  # Original mutual-information MINI profile.
    header = REPO / "examples/PolyBenchC-4.2.1/scientific/mutual-information/mutual-information.h"
    assert "define N 32" in header.read_text()
    diagonal = 0.5 / n + 0.5 / (n * n)
    off_diagonal = 0.5 / (n * n)
    expected = n * diagonal * np.log2(diagonal * n * n)
    expected += n * (n - 1) * off_diagonal * np.log2(off_diagonal * n * n)
    np.testing.assert_allclose(oracle.values, [expected], rtol=1e-10, atol=1e-12)


def scientific_expected(name: str, n: int, steps: int) -> NDArray[np.float64]:
    indices = np.arange(n)
    if name == "direct-dft":
        signal = (
            np.sin(2 * np.pi * 3 * indices / n)
            + 0.25 * np.cos(2 * np.pi * 5 * indices / n)
            + 0.01 * indices
        )
        transformed = np.fft.fft(signal)
        return np.column_stack([transformed.real, transformed.imag]).ravel()
    if name == "softened-nbody":
        mass = 1.0 + (indices % 7) * 0.125
        position = np.sin((indices[:, None] + 1) * np.arange(1, 4) * 0.37) + 0.01 * indices[:, None]
        delta = position[None, :, :] - position[:, None, :]
        squared = 0.01 + np.sum(delta * delta, axis=2)
        weight = mass[None, :] / (squared * np.sqrt(squared))
        np.fill_diagonal(weight, 0)
        return np.sum(weight[:, :, None] * delta, axis=1).ravel()
    if name == "lorenz-rk4":
        state = 1.0 + 0.01 * indices[:, None] + 0.1 * np.arange(3)

        def rhs(y: NDArray[np.float64]) -> NDArray[np.float64]:
            x, v, z = y.T
            return np.column_stack([10 * (v - x), x * (28 - z) - v, x * v - (8 / 3) * z])

        for _ in range(steps):
            k1 = rhs(state)
            k2 = rhs(state + 0.0005 * k1)
            k3 = rhs(state + 0.0005 * k2)
            k4 = rhs(state + 0.001 * k3)
            state += 0.001 * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        return state.ravel()
    matrix = 2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
    x = np.zeros(n)
    r = 1.0 + np.sin(0.3 * (indices + 1))
    p = r.copy()
    rr = r @ r
    for _ in range(10):
        ap = matrix @ p
        alpha = rr / (p @ ap)
        x += alpha * p
        r -= alpha * ap
        next_rr = r @ r
        p = r + (next_rr / rr) * p
        rr = next_rr
    return x


@pytest.mark.parametrize("name", ["direct-dft", "softened-nbody", "lorenz-rk4", "poisson-cg"])
@pytest.mark.parametrize(
    "profile,n,steps", [("mini", 32, 20), ("small", 64, 50), ("medium", 128, 100)]
)
def test_scientific_reference_independently(
    tmp_path: Path, name: str, profile: str, n: int, steps: int
) -> None:
    cc = shutil.which("gcc")
    if not cc:
        pytest.skip("C compiler unavailable")
    executable = tmp_path / "reference"
    subprocess.run(
        [
            cc,
            "-std=c99",
            "-O0",
            "-ffp-contract=off",
            f"-D{profile.upper()}_DATASET",
            str(SCIENCE / f"{name}.c"),
            "-lm",
            "-o",
            str(executable),
        ],
        check=True,
        capture_output=True,
    )
    output = subprocess.run([str(executable)], text=True, capture_output=True, check=True)
    actual = np.fromstring(output.stdout, sep="\n")
    np.testing.assert_allclose(actual, scientific_expected(name, n, steps), rtol=1e-10, atol=1e-12)
