from __future__ import annotations

from typing import TYPE_CHECKING

from lassi_x.skills import SKILL_NAMES, doctor_skills, install_skills, uninstall_skills

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
