"""Kernel/model/policy-scoped repair history, hypotheses and immutable input contracts."""

from __future__ import annotations

import ast
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class RepairProposalError(ValueError):
    """An invalid model proposal, not a backend/configuration failure."""


def input_contract(source: str) -> str:
    """Freeze build_inputs and its top-level dependencies, not editable forward code."""
    tree = ast.parse(source)
    definitions: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                definitions[alias.asname or alias.name.split(".")[0]] = node
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            definitions[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                if isinstance(target, ast.Name):
                    definitions[target.id] = node
    if "build_inputs" not in definitions:
        raise ValueError("repair requires a frozen build_inputs function")
    pending = ["build_inputs"]
    selected: dict[str, str] = {}
    while pending:
        name = pending.pop()
        if name in selected or name not in definitions:
            continue
        definition = definitions[name]
        selected[name] = ast.dump(definition, include_attributes=False)
        pending.extend(x.id for x in ast.walk(definition) if isinstance(x, ast.Name))
    # Import changes can redirect a helper even with unchanged builder text.
    return digest(json.dumps(selected, sort_keys=True).encode())


def parse_hypothesis(text: str, allowed: list[str]) -> dict[str, str]:
    try:
        data = json.loads(text.strip().removeprefix("```json").removesuffix("```").strip())
    except json.JSONDecodeError as exc:
        raise RepairProposalError("repair hypothesis must be valid JSON") from exc
    fields = (
        "technique",
        "failure_mechanism",
        "transformation",
        "semantics_argument",
        "arithmetic_plan",
        "strategy_key",
        "novelty",
    )
    if not isinstance(data, dict) or any(
        not isinstance(data.get(key), str) or not data[key].strip() for key in fields
    ):
        raise RepairProposalError("repair hypothesis must provide all required nonempty fields")
    if data["technique"] not in allowed:
        raise RepairProposalError("repair hypothesis selected a forbidden technique")
    if not isinstance(data.get("revisit_reason", ""), str):
        raise RepairProposalError("revisit_reason must be an explanation string")
    return {key: str(data.get(key, "")).strip() for key in (*fields, "revisit_reason")}


class RepairHistory:
    """Immutable event files prevent concurrent candidate flows overwriting history."""

    def __init__(self, root: Path, scope: dict[str, Any]) -> None:
        self.scope = scope
        self.root = root / digest(json.dumps(scope, sort_keys=True, default=str).encode())
        self.root.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[dict[str, Any]]:
        return [json.loads(p.read_text()) for p in sorted(self.root.glob("*.json"))]

    def reject_repetition(self, hypothesis: dict[str, str]) -> None:
        key = hypothesis["strategy_key"].casefold()
        if any(
            e.get("hypothesis", {}).get("strategy_key", "").casefold() == key
            for e in self.entries()
        ) and not hypothesis.get("revisit_reason"):
            raise RepairProposalError(
                "strategy already attempted; a specific revisit_reason is required"
            )

    def record(self, source: bytes, event: dict[str, Any]) -> dict[str, Any]:
        event_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%f") + "-" + uuid.uuid4().hex
        source_path = self.root / f"{event_id}.py"
        source_path.write_bytes(source)
        record = {
            **event,
            "scope": self.scope,
            "source_sha256": digest(source),
            "source_file": source_path.name,
            "event_id": event_id,
        }
        path = self.root / f"{event_id}.json"
        path.write_text(json.dumps(record, indent=2, default=str) + "\n")
        return record

    def repeated_source(self, fingerprint: str) -> bool:
        return any(e.get("semantic_fingerprint") == fingerprint for e in self.entries())
