from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

from lassi_x.types import Measurement, Status
from lassi_x.visualization import render_pareto_svg, write_pareto_visualizations

if TYPE_CHECKING:
    from pathlib import Path


def point(
    candidate: str,
    backend: str,
    latency: float,
    error: float,
    *,
    precision: str = "fp16",
    status: Status = Status.OK,
) -> Measurement:
    """Build one compact visualization fixture."""
    return Measurement(
        kernel="kernel",
        candidate_id=candidate,
        variant_id=f"{candidate}-base",
        backend=backend,
        precision=precision,
        compensation="none",
        status=status,
        module_path="candidate.py",
        storage_precision=precision,
        operator_precision=precision,
        accumulator_precision=precision,
        output_precision=precision,
        resource=f"{backend}-resource",
        latency_s=latency,
        max_rel_error=error,
    )


def test_render_svg_handles_zero_error_and_escapes_labels() -> None:
    svg = render_pareto_svg(
        [
            point("c&1", "cpu<local>", 1e-5, 1e-4, precision="fp64"),
            point("c2", "cpu<local>", 2e-5, 0.0, precision="fp32"),
        ],
        title="Test <frontier>",
        category_mode="precision",
    )
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "exact zero shown" in svg
    assert "Test &lt;frontier&gt;" in svg
    assert 'data-frontier="true"' in svg
    assert 'data-shape="circle"' in svg
    assert 'data-shape="square"' in svg


def test_write_visualizations_emits_overall_and_per_device_artifacts(tmp_path: Path) -> None:
    measurements = [
        point("c1", "cpu", 1e-5, 1e-3, precision="fp64"),
        point("c2", "cpu", 2e-5, 2e-3, precision="fp32"),
        point("c3", "cpu", 3e-5, 0.0, precision="bf16"),
        point("c1", "gpu/device", 5e-6, 3e-3),
        point("bad", "gpu/device", 0.0, 0.0),
        point("unsupported", "groq", 1e-6, 1e-3, status=Status.UNSUPPORTED),
    ]
    output = tmp_path / "visualizations"
    manifest = write_pareto_visualizations(output, measurements)

    assert manifest["overall"]["valid_points"] == 4
    assert manifest["overall"]["frontier_points"] == 3
    assert manifest["variant_markers"] == {
        "c1-base": "circle",
        "c2-base": "square",
        "c3-base": "triangle-up",
    }
    assert (output / "pareto-overall.svg").is_file()
    assert (output / "pareto-cpu.svg").is_file()
    assert (output / "pareto-gpu-device.svg").is_file()
    assert not (output / "pareto-groq.svg").exists()
    ET.parse(output / "pareto-overall.svg")
    ET.parse(output / "pareto-cpu.svg")

    data = json.loads((output / "frontiers.json").read_text())
    assert set(data["devices"]) == {"cpu", "gpu/device"}
    assert len(data["overall"]) == 3
    assert json.loads((output / "manifest.json").read_text()) == manifest
