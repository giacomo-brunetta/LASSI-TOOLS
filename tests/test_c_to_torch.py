from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import torch
import yaml

from lassi_x.c_fixtures import FixtureSpec
from lassi_x.c_to_torch import (
    SYSTEM_PROMPT,
    TranslationPlan,
    _bundle,
    c_gate,
    load_plan,
    prompt,
    source_diff,
    translate,
)
from lassi_x.candidate_runner import load_module
from lassi_x.config import RunConfig
from lassi_x.hermes import HermesTurn
from lassi_x.types import Usage

from .test_config import minimal_config

pytestmark = pytest.mark.skipif(shutil.which("clang") is None, reason="Clang unavailable")

SOURCE = """void compute(int m, int n, double A[2][3], double x[3], double y[2]) {
  int i, j;
  for(i=0;i<m;i++) y[i]=0;
  for(i=0;i<m;i++)
    for(j=0;j<n;j++) y[i] += A[i][j]*x[j];
}
int main(void) {
 int m=2,n=3;
 double A[2][3]={{1,2,3},{4,5,6}},x[3]={2,3,4},y[2]={0,0};
 /* START */
 compute(m,n,A,x,y);
 /* END */
 return 0;
}
"""


def setup(tmp_path: Path) -> tuple[TranslationPlan, RunConfig, Path]:
    original = tmp_path / "tiny.c"
    original.write_text(SOURCE)
    spec: dict[str, Any] = {
        "before": "/* START */",
        "after": "/* END */",
        "inputs": {
            name: {"argument": name, "access": "read_only", "scalar": name in "mn"}
            for name in ("m", "n", "A", "x")
        },
        "outputs": ["y"],
        "fields": {
            "A": {"expression": "A", "shape": ["2", "3"]},
            "x": {"expression": "x", "shape": ["3"]},
            "y": {"expression": "y", "shape": ["2"]},
        },
    }
    spec["inputs"]["y"] = {"argument": "y_initial", "access": "read_write"}
    (tmp_path / "spec.yaml").write_text(yaml.safe_dump(spec))
    data = minimal_config(tmp_path)
    data["oracle"]["build"][0] = "clang"
    data["oracle"]["fixture_spec"] = "spec.yaml"
    config = RunConfig.model_validate(data)
    config_path = tmp_path / "case.yaml"
    config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")))
    plan = TranslationPlan(
        cases=[config_path],
        function="compute",
        model={"model": "unused"},
        native_python=Path("/unused/python"),
        tenspiler_root=tmp_path,
        llvm_bin=tmp_path,
        llvm_pass=tmp_path / "pass.so",
        proposals=1,
    )
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps({"source": SOURCE, "changes": []}))
    return plan, config, proposal


def test_edit_record_has_no_size_or_body_restriction(tmp_path: Path) -> None:
    plan, _, _ = setup(tmp_path)
    candidate = tmp_path / "adapted.c"
    broader = "/* A broader representation adaptation. */\n" * 100
    candidate.write_text(broader + SOURCE.replace("void compute", "static void compute"))
    diff = source_diff(tmp_path / "tiny.c", candidate)
    assert diff.count("+/* A broader representation adaptation.") == 100
    assert "+static void compute" in diff
    assert "maximum_changed_lines" not in json.loads(prompt(plan, SOURCE))
    assert "minimal changes are a preference, not an acceptance rule" in SYSTEM_PROMPT
    assert "There is no edit-size limit or kernel-body boundary" in SYSTEM_PROMPT


def test_legacy_budget_is_ignored_and_not_exported(tmp_path: Path) -> None:
    plan, _, _ = setup(tmp_path)
    legacy = plan.model_dump() | {"changed_lines": 1}
    restored = TranslationPlan.model_validate(legacy)
    assert "changed_lines" not in restored.model_dump()
    assert "changed_lines" not in TranslationPlan.model_json_schema()["properties"]


def test_c_gate_detects_bad_arithmetic_and_readonly_mutation(tmp_path: Path) -> None:
    _, config, _ = setup(tmp_path)
    candidate = tmp_path / "adapted.c"
    candidate.write_text(SOURCE.replace("y[i]=0", "y[i]=0.0"))
    assert asyncio.run(c_gate(config, candidate, tmp_path / "good"))["passed"]
    candidate.write_text(SOURCE.replace("A[i][j]*x[j]", "A[i][j]+x[j]"))
    assert not asyncio.run(c_gate(config, candidate, tmp_path / "bad"))["passed"]
    candidate.write_text(SOURCE.replace("  int i, j;", "  x[0] += 1;\n  int i, j;"))
    result = asyncio.run(c_gate(config, candidate, tmp_path / "mutated"))
    assert not result["passed"]
    assert any(row["read_only"] and not row["passed"] for row in result["checks"])


def test_c_failure_prevents_synthesis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan, _, proposal = setup(tmp_path)
    proposal.write_text(json.dumps({"source": SOURCE.replace("y[i]=0", "y[i]=1"), "changes": []}))

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("synthesis preparation reached despite failed C gate")

    monkeypatch.setattr("lassi_x.c_to_torch.prepare", forbidden)
    assert not asyncio.run(translate(plan, tmp_path / "run", proposal=proposal))
    result = json.loads((tmp_path / "run/result.json").read_text())
    assert result["attempts"][0]["stage"] == "c_validation"
    assert not (tmp_path / "run/candidate.py").exists()


@pytest.mark.parametrize("bad_torch", [False, True])
def test_replay_runs_both_real_gates_with_stub_synthesis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_torch: bool
) -> None:
    plan, _, proposal = setup(tmp_path)
    proposal.write_text(
        json.dumps(
            {
                "source": "/* broader adaptation */\n" * 100
                + SOURCE.replace("void compute", "static void compute"),
                "changes": ["Add declarations outside the old body boundary."],
            }
        )
    )

    async def synthesize(command: list[str], **kwargs: Any) -> tuple[int, str, str]:
        assert "--bounded-only" in command
        directory = Path(command[command.index("--run-dir") + 1])
        directory.mkdir()
        operation = "torch.zeros_like(A[:,0])" if bad_torch else "A @ x"
        (directory / "stage_y_torch.py").write_text(
            f"import torch\ndef stage_y_torch(A, x):\n    return {operation}\n"
        )
        return 0, "stub synthesis, real numerical gates", ""

    monkeypatch.setattr("lassi_x.c_to_torch._run", synthesize)
    output = tmp_path / "run"
    assert asyncio.run(translate(plan, output, proposal=proposal)) is not bad_torch
    result = json.loads((output / "result.json").read_text())
    assert result["extended_composition"] is False
    assert result["passed"] is not bad_torch
    if bad_torch:
        assert result["attempts"][0]["stage"] == "torch_validation"
        assert not (output / "candidate.py").exists()
    else:
        assert "y_initial" in (output / "candidate.py").read_text()
    assert (output / "attempt-1/changes.diff").exists()


def test_plan_keeps_venv_python_symlink(tmp_path: Path) -> None:

    plan, _, _ = setup(tmp_path)
    executable = tmp_path / "venv-python"
    executable.symlink_to("/usr/bin/python3")
    plan = plan.validated_update(native_python=executable)
    path = tmp_path / "plan.yaml"
    path.write_text(yaml.safe_dump(plan.model_dump(mode="json")))
    loaded = load_plan(path)
    assert loaded.native_python == executable
    assert loaded.native_python.is_symlink()


def test_wrapper_reorders_outputs_by_fixture_name(tmp_path: Path) -> None:

    prepared, synthesized = tmp_path / "prepared", tmp_path / "synthesized"
    prepared.mkdir()
    synthesized.mkdir()
    (prepared / "manifest.json").write_text(
        json.dumps(
            {
                "program": {
                    "inputs": ["A", "x"],
                    "outputs": ["y", "z"],
                    "stages": [
                        {
                            "output": "y",
                            "matrix": "A",
                            "vector": "x",
                            "rows": "m",
                            "columns": "n",
                            "transpose": False,
                        },
                        {
                            "output": "z",
                            "matrix": "A",
                            "vector": "y",
                            "rows": "m",
                            "columns": "n",
                            "transpose": False,
                        },
                    ],
                }
            }
        )
    )
    for output in ("y", "z"):
        (synthesized / f"stage_{output}_torch.py").write_text(
            f"def stage_{output}_torch(A,x):\n    return A @ x\n"
        )
    spec = FixtureSpec(
        inputs={
            name: {"argument": f"arg_{name}", "access": "read_only", "scalar": name in "mn"}
            for name in ("m", "n", "A", "x")
        },
        outputs=["z", "y"],
    )
    destination = tmp_path / "candidate.py"
    _bundle(prepared, synthesized, spec, destination)
    model = load_module(destination)
    z, y = model.forward(2, 2, torch.eye(2) * 2, torch.ones(2))
    assert torch.equal(y, torch.full((2,), 2.0))
    assert torch.equal(z, torch.full((2,), 4.0))


def test_model_adaptation_budget_and_feedback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    plan, _, _ = setup(tmp_path)
    calls: list[str] = []

    class Session:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            assert kwargs["toolsets"] == []

        async def send(self, text: str) -> HermesTurn:
            calls.append(text)
            return HermesTurn(
                json.dumps(
                    {
                        "source": SOURCE.replace("y[i]=0", "y[i]=1"),
                        "changes": ["incorrect adaptation"],
                    }
                ),
                Usage(),
            )

        async def close(self) -> None:
            pass

    monkeypatch.setattr("lassi_x.c_to_torch.HermesSession", Session)
    assert not asyncio.run(translate(plan.validated_update(proposals=2), tmp_path / "model-run"))
    assert len(calls) == 2
    assert "adapted C failed case" in calls[1]
    assert (tmp_path / "model-run/attempt-2/usage.json").exists()
