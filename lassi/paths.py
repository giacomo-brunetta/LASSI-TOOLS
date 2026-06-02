from __future__ import annotations

from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
RESOURCES_ROOT = REPO_ROOT / "resources"
PROMPTS_ROOT = RESOURCES_ROOT / "prompts"
COMPATIBILITY_ROOT = RESOURCES_ROOT / "compatibility"
SODA_TOOLS_ROOT = REPO_ROOT / "soda-tools"


def prompt_resource_path(name: str) -> Path:
    return PROMPTS_ROOT / name
