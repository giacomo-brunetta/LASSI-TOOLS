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
    "lassi-x-translate-kernel",
    "lassi-x-repair-candidate",
    "lassi-x-compare-outputs",
    "lassi-x-summarize-output",
    "lassi-x-machine-info",
    "lassi-x-gpu-info",
    "lassi-x-toolchain-info",
    "lassi-x-run-benchmark",
    "lassi-x-fp16-compensate",
    "lassi-x-groq-latency",
    "lassi-x-pareto-explore",
    "lassi-x-verification-report",
)

AUTOMATION_SKILLS = (
    "lassi-x-translate-kernel",
    "lassi-x-repair-candidate",
    "lassi-x-compare-outputs",
    "lassi-x-machine-info",
    "lassi-x-fp16-compensate",
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
            if sync and old_hash and target_hash != old_hash:
                conflicts.append(relative)
                continue
            if not sync:
                conflicts.append(relative)
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        installed.append(relative)
    hashes = {
        relative: _hash(destination / relative)
        for relative in source_files
        if (destination / relative).is_file()
    }
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
    return {
        "ok": not missing and not invalid,
        "root": str(root),
        "found": found,
        "missing": missing,
        "invalid": invalid,
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
