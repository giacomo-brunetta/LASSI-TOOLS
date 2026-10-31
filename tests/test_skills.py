from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest
import yaml
from agent.prompt_builder import _skill_should_show  # type: ignore[import-untyped]
from agent.skill_utils import extract_skill_conditions  # type: ignore[import-untyped]

from lassi_x.instruction_provenance import assembled_system_prompt, save_instruction_snapshot
from lassi_x.skills import (
    SKILL_NAMES,
    automation_skill_prompt,
    doctor_skills,
    install_skills,
    require_automation_skills,
    require_bundled_skills,
    source_root,
    uninstall_skills,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_skill_install_doctor_and_uninstall(tmp_path: Path) -> None:
    installed = install_skills(tmp_path)
    assert installed["ok"]
    doctor = doctor_skills(tmp_path)
    assert doctor["ok"]
    assert set(doctor["found"]) == set(SKILL_NAMES)
    removed = uninstall_skills(tmp_path)
    assert removed["ok"]
    assert not doctor_skills(tmp_path)["ok"]


def test_bundled_skills_define_roles_evidence_and_guardrails() -> None:
    for name in SKILL_NAMES:
        text = (source_root() / name / "SKILL.md").read_text()
        _, raw_frontmatter, body = text.split("---", 2)
        frontmatter = yaml.safe_load(raw_frontmatter)

        assert frontmatter["name"] == name
        assert frontmatter["description"]
        assert "requires_toolsets" not in frontmatter
        assert frontmatter["metadata"]["hermes"]["requires_toolsets"]
        assert "## Role" in body
        assert "## Workflow" in body
        assert "## Evidence standard" in body
        assert "## Guardrails" in body
        assert "LASSI-X" not in text


def test_output_sensitive_skills_require_bounded_diagnostics() -> None:
    output_sensitive = {
        "lassi-x-accelerator-compatibility",
        "lassi-x-compare-outputs",
        "lassi-x-elementary-function-audit",
        "lassi-x-fp-error-diagnose",
        "lassi-x-fp16-compensate",
        "lassi-x-groq-latency",
        "lassi-x-pareto-explore",
        "lassi-x-repair-candidate",
        "lassi-x-run-benchmark",
        "lassi-x-summarize-output",
        "lassi-x-translate-kernel",
        "lassi-x-verification-report",
    }

    for name in output_sensitive:
        text = (source_root() / name / "SKILL.md").read_text()
        assert "## Bounded diagnostics" in text
        assert "8 KiB" in text


def test_skill_checks_detect_stale_auxiliary_resources(tmp_path: Path) -> None:
    installed = install_skills(tmp_path)
    resource = tmp_path / "skills/lassi-x/lassi-x-fp16-compensate/references/techniques.md"
    resource.write_text("stale recommendations")
    assert not doctor_skills(tmp_path)["ok"]
    assert installed["ok"]
    with pytest.raises(RuntimeError, match="stale or incomplete"):
        require_automation_skills(tmp_path)


def test_numerical_worker_receives_full_skills_and_technique_reference() -> None:
    prompt = automation_skill_prompt("compensation-n-c1-fp16")
    for name in (
        "lassi-x-fp-error-diagnose",
        "lassi-x-fp16-compensate",
        "lassi-x-elementary-function-audit",
    ):
        assert (source_root() / name / "SKILL.md").read_text() in prompt
    assert (
        source_root() / "lassi-x-fp16-compensate/references/techniques.md"
    ).read_text() in prompt
    assert automation_skill_prompt("unrelated-test-role") == ""


@pytest.mark.parametrize("operation", ["install", "sync"])
def test_conflicts_never_become_owned_on_repeated_operations(
    tmp_path: Path, operation: str
) -> None:
    install_skills(tmp_path)
    target = tmp_path / "skills/lassi-x/lassi-x-translate-kernel/SKILL.md"
    target.write_text("local edits")
    for _ in range(3):
        result = install_skills(tmp_path, sync=operation == "sync")
        assert "lassi-x-translate-kernel/SKILL.md" in result["conflicts"]
        assert target.read_text() == "local edits"
    removed = uninstall_skills(tmp_path)
    assert "lassi-x-translate-kernel/SKILL.md" in removed["modified"]
    assert target.read_text() == "local edits"


@pytest.mark.parametrize("sync", [False, True])
def test_unowned_conflict_remains_unowned(tmp_path: Path, sync: bool) -> None:
    target = tmp_path / "skills/lassi-x/lassi-x-translate-kernel/SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("preexisting local skill")
    for _ in range(2):
        assert not install_skills(tmp_path, sync=sync)["ok"]
    uninstall_skills(tmp_path)
    assert target.read_text() == "preexisting local skill"


def test_bundle_validation_ignores_global_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "missing"))
    require_bundled_skills()


def test_skills_are_discoverable_with_workspace_toolsets() -> None:
    for name in SKILL_NAMES:
        text = (source_root() / name / "SKILL.md").read_text()
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        assert _skill_should_show(
            extract_skill_conditions(frontmatter),
            {"skills_list", "skill_view", "mcp_lassi_workspace_run_command"},
            {"skills", "lassi-x-workspace"},
        ), name


def test_instruction_snapshot_captures_exact_injected_text_and_all_resources(
    tmp_path: Path,
) -> None:
    home = tmp_path / "profile"
    path = save_instruction_snapshot(
        tmp_path, system="role policy", role="c1", toolsets=["skills"], home=home
    )
    record = json.loads(path.read_text())
    assert record["system_prompt"] == assembled_system_prompt("role policy", "c1", ["skills"], home)
    assert record["system_sha256"] == hashlib.sha256(record["system_prompt"].encode()).hexdigest()
    assert "lassi-x-fp16-compensate/references/techniques.md" in record["skill_files"]
    assert "lassi-x-fp16-compensate/scripts/torch_cpu_techniques.py" in record["skill_files"]
    assert "precision_policy.py" in record["prompt_sources"]
    assert str(tmp_path / "profile/skills/lassi-x") in record["system_prompt"]
    assert (
        save_instruction_snapshot(
            tmp_path, system="role policy", role="c1", toolsets=["skills"], home=home
        )
        == path
    )
    assert (
        save_instruction_snapshot(
            tmp_path, system="new policy", role="c1", toolsets=["skills"], home=home
        )
        != path
    )
    assert path.exists()


def test_sync_updates_owned_unmodified_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import lassi_x.skills as skills  # noqa: PLC0415

    source = tmp_path / "source"
    source.mkdir()
    (source / "SKILL.md").write_text("original")
    monkeypatch.setattr(skills, "source_root", lambda: source)
    home = tmp_path / "home"
    assert install_skills(home)["ok"]
    (source / "SKILL.md").write_text("updated")
    result = install_skills(home, sync=True)
    assert result["ok"]
    assert result["installed"] == ["SKILL.md"]
    assert (home / "skills/lassi-x/SKILL.md").read_text() == "updated"
    assert uninstall_skills(home)["ok"]
