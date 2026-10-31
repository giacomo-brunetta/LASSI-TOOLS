from __future__ import annotations

import contextlib
import hashlib
import json
import os
import shutil
from importlib.resources import files
from pathlib import Path
from typing import Any

from . import __version__
from .artifacts import atomic_write

SKILL_NAMES = (
    "lassi-x-accelerator-compatibility",
    "lassi-x-translate-kernel",
    "lassi-x-repair-candidate",
    "lassi-x-compare-outputs",
    "lassi-x-summarize-output",
    "lassi-x-machine-info",
    "lassi-x-gpu-info",
    "lassi-x-toolchain-info",
    "lassi-x-run-benchmark",
    "lassi-x-fp-error-diagnose",
    "lassi-x-fp16-compensate",
    "lassi-x-elementary-function-audit",
    "lassi-x-groq-latency",
    "lassi-x-pareto-explore",
    "lassi-x-verification-report",
)

AUTOMATION_SKILLS = (
    "lassi-x-accelerator-compatibility",
    "lassi-x-translate-kernel",
    "lassi-x-repair-candidate",
    "lassi-x-compare-outputs",
    "lassi-x-machine-info",
    "lassi-x-fp-error-diagnose",
    "lassi-x-fp16-compensate",
    "lassi-x-elementary-function-audit",
)


def hermes_home(path: Path | None = None) -> Path:
    if path is not None:
        return path.expanduser().resolve()
    return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser().resolve()


def source_root() -> Path:
    return Path(str(files("lassi_x").joinpath("resources", "hermes_skills")))


def install_root(home: Path | None = None) -> Path:
    return hermes_home(home) / "skills" / "lassi-x"


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_files() -> dict[str, Path]:
    root = source_root()
    return {str(path.relative_to(root)): path for path in root.rglob("*") if path.is_file()}


def install_skills(home: Path | None = None, *, sync: bool = False) -> dict[str, Any]:
    destination = install_root(home)
    manifest_path = destination / ".lassi-x-manifest.json"
    old_manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    old_hashes = old_manifest.get("files") or {}
    source_files = _source_files()
    installed: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []
    destination.mkdir(parents=True, exist_ok=True)
    for relative, source in source_files.items():
        target = destination / relative
        source_hash = _hash(source)
        if target.is_file():
            target_hash = _hash(target)
            old_hash = old_hashes.get(relative)
            if target_hash == source_hash:
                unchanged.append(relative)
                continue
            if sync and target_hash != old_hash:
                conflicts.append(relative)
                continue
            if not sync:
                conflicts.append(relative)
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        installed.append(relative)
    # Conflicts remain unowned (or retain their last installed baseline). Never
    # adopt a local edit as the baseline: a later sync would overwrite it.
    hashes = dict(old_hashes)
    for relative in installed + unchanged:
        hashes[relative] = _hash(source_files[relative])
    manifest = {
        "schema_version": 1,
        "lassi_x_version": __version__,
        "files": hashes,
    }
    atomic_write(manifest_path, json.dumps(manifest, indent=2) + "\n")
    return {
        "ok": not conflicts,
        "root": str(destination),
        "installed": installed,
        "unchanged": unchanged,
        "conflicts": conflicts,
    }


def doctor_skills(home: Path | None = None) -> dict[str, Any]:
    root = install_root(home)
    found: list[str] = []
    missing: list[str] = []
    invalid: list[str] = []
    for name in SKILL_NAMES:
        skill = root / name / "SKILL.md"
        if not skill.is_file():
            missing.append(name)
            continue
        text = skill.read_text(errors="replace")
        if not text.startswith("---\n") or f"name: {name}" not in text:
            invalid.append(name)
        else:
            found.append(name)
    stale_files = [
        relative
        for relative, source in _source_files().items()
        if not (root / relative).is_file() or _hash(root / relative) != _hash(source)
    ]
    return {
        "ok": not missing and not invalid and not stale_files,
        "root": str(root),
        "found": found,
        "missing": missing,
        "invalid": invalid,
        "stale_files": stale_files,
    }


def require_automation_skills(home: Path | None = None) -> None:
    root = install_root(home)
    missing = [name for name in AUTOMATION_SKILLS if not (root / name / "SKILL.md").is_file()]
    if missing:
        raise RuntimeError(
            "Required Hermes skills are unavailable: "
            + ", ".join(missing)
            + ". Run: lassi-x skills install"
        )
    stale = [
        relative
        for relative, source in _source_files().items()
        if relative.split("/", 1)[0] in AUTOMATION_SKILLS
        and (not (root / relative).is_file() or _hash(root / relative) != _hash(source))
    ]
    if stale:
        raise RuntimeError(
            "Required Hermes skill content is stale or incomplete: "
            + ", ".join(stale)
            + ". Run: lassi-x skills sync"
        )


def require_bundled_skills() -> None:
    """Validate the package copied into workers, independently of global installs."""
    root = source_root()
    missing = [name for name in SKILL_NAMES if not (root / name / "SKILL.md").is_file()]
    if missing:
        raise RuntimeError("Bundled Hermes skills are incomplete: " + ", ".join(missing))
    # Required inline references must also be present before a run starts.
    for role in ("planner", "c1", "compensation-check", "compatibility-check"):
        automation_skill_prompt(role)


def automation_skill_prompt(role: str, home: Path | None = None) -> str:
    """Supply full task-relevant instructions without relying on voluntary skill loading.

    Other installed skills remain available through the skill tool. Required numerical
    technique guidance is inline too; executable templates remain tool-accessible files.
    """
    names: tuple[str, ...]
    if role.startswith("compensation-"):
        names = (
            "lassi-x-fp-error-diagnose",
            "lassi-x-fp16-compensate",
            "lassi-x-elementary-function-audit",
        )
    elif role.startswith("compatibility-"):
        names = ("lassi-x-accelerator-compatibility", "lassi-x-repair-candidate")
    elif role == "planner":
        names = ("lassi-x-accelerator-compatibility", "lassi-x-translate-kernel")
    elif role.startswith("c") and role[1:].isdigit():
        names = (
            "lassi-x-translate-kernel",
            "lassi-x-repair-candidate",
            "lassi-x-compare-outputs",
            "lassi-x-accelerator-compatibility",
            "lassi-x-elementary-function-audit",
        )
    else:
        return ""
    root = source_root()
    resources = [f"{name}/SKILL.md" for name in names]
    if "lassi-x-fp16-compensate" in names:
        resources.append("lassi-x-fp16-compensate/references/techniques.md")
    if "lassi-x-accelerator-compatibility" in names:
        resources.append("lassi-x-accelerator-compatibility/references/platform-summary.md")
    parts = [
        "Required skill instructions (supplied in full by the harness):\n"
        "The experiment's explicit precision contract overrides generic wider-arithmetic "
        "examples or capability-based recommendations in these skills.\n"
        f"Installed skill root: {install_root(home)}\n"
        "Use the enabled skills tool for other skills, references and scripts.\n"
        "Use only the assigned tools. A skill does not grant additional tools or file scope. "
        "If a required command or capability is unavailable, report that limitation; "
        "do not substitute another machine or toolset without authorization."
    ]
    for relative in resources:
        path = root / relative
        parts.append(f"\n--- Skill resource: {relative} ---\n{path.read_text()}")
    return "\n".join(parts)


def uninstall_skills(home: Path | None = None) -> dict[str, Any]:
    root = install_root(home)
    manifest_path = root / ".lassi-x-manifest.json"
    if not manifest_path.is_file():
        return {"ok": True, "root": str(root), "removed": [], "modified": []}
    manifest = json.loads(manifest_path.read_text())
    removed: list[str] = []
    modified: list[str] = []
    for relative, expected_hash in (manifest.get("files") or {}).items():
        target = root / relative
        if not target.is_file():
            continue
        if _hash(target) != expected_hash:
            modified.append(relative)
            continue
        target.unlink()
        removed.append(relative)
    manifest_path.unlink()
    for directory in sorted(
        (path for path in root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        with contextlib.suppress(OSError):
            directory.rmdir()
    with contextlib.suppress(OSError):
        root.rmdir()
    return {
        "ok": not modified,
        "root": str(root),
        "removed": removed,
        "modified": modified,
    }
