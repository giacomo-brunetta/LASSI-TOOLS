from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from lassi_x.skills import (
    SKILL_NAMES,
    doctor_skills,
    install_skills,
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
