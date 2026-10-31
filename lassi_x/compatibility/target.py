"""Machine-target configuration and compiler-checker loading."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from lassi_x.compatibility.fixtures import PRECISION_DTYPES


class TargetConfig(BaseModel):
    """Fail early on malformed compiler settings instead of coercing them."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)

    schema_version: Literal[1]
    target_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    family: str = Field(min_length=1)
    description: str = ""
    checker: str = Field(pattern=r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")
    precisions: list[str] = Field(min_length=1)
    timeout_s: float = Field(default=300.0, gt=0)
    max_workers: int = Field(default=1, gt=0)
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("precisions")
    @classmethod
    def known_precisions(cls, values: list[str]) -> list[str]:
        if set(values) - set(PRECISION_DTYPES):
            raise ValueError("unknown target precisions")
        if len(values) != len(set(values)):
            raise ValueError("duplicate target precisions")
        return values


def load_target(path: str | Path) -> dict[str, Any]:
    target_path = Path(path)
    if target_path.is_dir():
        target_path = target_path / "target.yaml"
    payload = TargetConfig.model_validate(
        yaml.safe_load(target_path.read_text(encoding="utf-8"))
    ).model_dump()
    payload["config_path"] = str(target_path.resolve())
    return payload


def checker_class(target: dict[str, Any]) -> type[Any]:
    module_name, separator, attribute = str(target["checker"]).partition(":")
    if not separator:
        raise ValueError("target checker must use module:Class syntax")
    module = importlib.import_module(module_name)
    checker = getattr(module, attribute)
    return cast("type[Any]", checker)
