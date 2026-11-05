"""Repository CLI entry point for frozen deterministic Stage 2 replay."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import argparse

from pydantic import TypeAdapter
from torch import fx

from lassi_x.stage2_deterministic import Plan, Proposal, implementation_identity, run


def execute(config_path: Path, output: Path) -> int:
    """Load an explicitly trusted, hash-bound capture/validation driver and replay."""
    config = json.loads(config_path.read_text())
    required = {"schema", "source", "plan", "contract", "environment", "driver", "driver_sha256"}
    if set(config) != required or config["schema"] != 1:
        raise ValueError("Invalid Stage 2 configuration schema")
    if output.exists():
        raise FileExistsError("Refusing to overwrite Stage 2 output")
    base = config_path.resolve().parent
    paths = {
        name: (base / config[name]).resolve() for name in required - {"schema", "driver_sha256"}
    }
    plan_data = json.loads(paths["plan"].read_text())
    if set(plan_data) - {f.name for f in fields(Plan)}:
        raise ValueError("Unknown plan field")
    if "implementation_sha256" not in plan_data:
        raise ValueError("Plan must freeze the adapter implementation identity")
    for item in plan_data.get("proposals", []):
        if set(item) - {f.name for f in fields(Proposal)}:
            raise ValueError("Unknown proposal field")
    plan = TypeAdapter(Plan).validate_json(paths["plan"].read_text(), strict=True)
    content = {
        name: paths[name].read_bytes() for name in ("source", "contract", "environment", "driver")
    }
    expected = {
        "source": plan.source_sha256,
        "contract": plan.contract_sha256,
        "environment": plan.environment_sha256,
        "driver": config["driver_sha256"],
    }
    if any(
        hashlib.sha256(content[name]).hexdigest() != digest for name, digest in expected.items()
    ):
        raise ValueError("Frozen input identity mismatch before driver execution")
    if plan.implementation_sha256 != implementation_identity():
        raise ValueError("Frozen implementation identity mismatch")
    namespace: dict[str, Any] = {
        "__name__": "lassi_stage2_driver",
        "__file__": str(paths["driver"]),
    }
    # Explicit trusted driver, not an automatically discovered candidate plugin.
    exec(compile(content["driver"], str(paths["driver"]), "exec", dont_inherit=True), namespace)
    build = namespace.get("build_graph")
    validator = namespace.get("validate")
    if not callable(build) or not callable(validator):
        raise ValueError("Driver must define build_graph(source, contract) and validate")
    graph = build(content["source"].decode(), content["contract"])
    if not isinstance(graph, fx.GraphModule):
        raise TypeError("Driver must return a Torch FX GraphModule")
    selected = run(
        graph,
        plan,
        source=content["source"].decode(),
        contract=content["contract"],
        environment=content["environment"],
        output=output,
        validate=validator,
    )
    (output / "driver.py").write_bytes(content["driver"])
    (output / "invocation.json").write_text(json.dumps(config, sort_keys=True, indent=2) + "\n")
    report = json.loads((output / "result.json").read_text())
    print(
        json.dumps(
            {
                "status": report["status"],
                "selected": report["selected"],
                "output": str(output.resolve()),
            },
            indent=2,
        )
    )
    return 0 if selected is not None else 1


def add_parser(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    stage = sub.add_parser("stage2", help="Frozen deterministic numerical repair replay")
    commands = stage.add_subparsers(dest="stage2_command", required=True)
    replay = commands.add_parser(
        "replay", help="Execute an explicit trusted frozen replay configuration"
    )
    replay.add_argument("config", type=Path)
    replay.add_argument("output", type=Path)
