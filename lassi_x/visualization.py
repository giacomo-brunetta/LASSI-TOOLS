"""Deterministic SVG artifacts for latency/error Pareto frontiers."""

from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from .artifacts import atomic_write, write_json
from .pareto import frontier_indices, valid_point

if TYPE_CHECKING:
    from pathlib import Path

    from .types import Measurement

_SVG = "http://www.w3.org/2000/svg"
_PALETTE = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#000000",
)
_PRECISION_ORDER = {"fp64": 0, "fp32": 1, "bf16": 2, "fp16": 3}
_MARKER_SHAPES = (
    "circle",
    "square",
    "triangle-up",
    "diamond",
    "triangle-down",
    "pentagon",
    "hexagon",
    "star",
)


@dataclass(frozen=True, slots=True)
class _PlotPoint:
    """Measurement plus plot coordinates and frontier membership."""

    measurement: Measurement
    x: float
    y: float
    frontier: bool


def _slug(value: str) -> str:
    """Convert a backend name to a safe, stable filename component.

    Args:
        value: Human-readable backend identifier.

    Returns:
        Lowercase filename component with a digest fallback.

    """
    clean = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return clean or f"backend-{hashlib.sha256(value.encode()).hexdigest()[:8]}"


def _backend_slugs(backends: list[str]) -> dict[str, str]:
    """Assign collision-free artifact slugs to backend names.

    Args:
        backends: Unique backend names.

    Returns:
        Mapping from each backend name to its artifact slug.

    """
    result: dict[str, str] = {}
    used: set[str] = set()
    for backend in sorted(backends):
        base = _slug(backend)
        slug = base
        if slug in used:
            slug = f"{base}-{hashlib.sha256(backend.encode()).hexdigest()[:8]}"
        result[backend] = slug
        used.add(slug)
    return result


def _valid_measurements(points: list[Measurement]) -> list[Measurement]:
    """Return physically meaningful measurements eligible for plotting.

    Args:
        points: All measurement outcomes from a run.

    Returns:
        Successful points with positive latency and nonnegative error.

    """
    return [point for point in points if valid_point(point)]


def _frontier_points(points: list[Measurement]) -> list[Measurement]:
    """Return nondominated points from one plotting scope.

    Args:
        points: Measurements already scoped globally or to one backend.

    Returns:
        Points on the latency/error Pareto frontier.

    """
    return [points[index] for index in frontier_indices(points)]


def _latency_value(point: Measurement) -> float:
    """Return latency from a measurement already accepted by ``valid_point``."""
    assert point.latency_s is not None
    return point.latency_s


def _error_value(point: Measurement) -> float:
    """Return error from a measurement already accepted by ``valid_point``."""
    error = point.y_error
    assert error is not None
    return error


def _effective_errors(points: list[Measurement]) -> tuple[dict[int, float], float | None]:
    """Map exact zero errors to a visible floor for logarithmic plotting.

    Args:
        points: Valid measurements in one plot.

    Returns:
        Mapping keyed by object identity and the zero floor, or ``None`` when
        the plot contains no exact-zero errors.

    """
    errors = [_error_value(point) for point in points]
    positive = [error for error in errors if error > 0]
    has_zero = any(error == 0 for error in errors)
    if not has_zero:
        return {id(point): _error_value(point) for point in points}, None
    floor = min(positive) / 10 if positive else 1e-18
    return {
        id(point): floor if _error_value(point) == 0 else _error_value(point) for point in points
    }, floor


def _log_domain(values: list[float]) -> tuple[float, float]:
    """Build a padded base-10 logarithmic domain.

    Args:
        values: Strictly positive data values.

    Returns:
        Lower and upper domain bounds in log10 space.

    """
    low = math.log10(min(values))
    high = math.log10(max(values))
    if math.isclose(low, high):
        return low - 0.5, high + 0.5
    padding = max((high - low) * 0.08, 0.08)
    return low - padding, high + padding


def _log_ticks(low: float, high: float, maximum: int = 7) -> list[float]:
    """Choose readable power-of-ten ticks for a logarithmic domain.

    Args:
        low: Lower log10 domain bound.
        high: Upper log10 domain bound.
        maximum: Approximate maximum tick count.

    Returns:
        Tick values in linear space.

    """
    exponents = list(range(math.ceil(low), math.floor(high) + 1))
    if not exponents:
        exponents = [round((low + high) / 2)]
    step = max(1, math.ceil(len(exponents) / maximum))
    return [10.0**exponent for exponent in exponents[::step]]


def _latency_label(seconds: float) -> str:
    """Format seconds with an appropriate SI unit.

    Args:
        seconds: Positive latency in seconds.

    Returns:
        Compact tick label.

    """
    if seconds < 1e-6:
        return f"{seconds * 1e9:g} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:g} µs"
    if seconds < 1:
        return f"{seconds * 1e3:g} ms"
    return f"{seconds:g} s"


def _error_label(error: float) -> str:
    """Format a relative-error axis tick.

    Args:
        error: Nonnegative error value.

    Returns:
        Scientific-notation tick label.

    """
    return f"{error:.0e}"


def _point_label(point: Measurement) -> str:
    """Build a compact frontier annotation.

    Args:
        point: Measurement being annotated.

    Returns:
        Candidate, precision, and optional compensation label.

    """
    fields = [point.candidate_id, point.precision]
    if point.compensation != "none":
        fields.append(point.compensation)
    return " · ".join(fields)


def _point_tooltip(point: Measurement) -> str:
    """Build exact provenance text embedded in an SVG marker.

    Args:
        point: Measurement represented by the marker.

    Returns:
        Multi-field tooltip text.

    """
    latency = "n/a" if point.latency_s is None else f"{point.latency_s:.12g} s"
    error = "n/a" if point.y_error is None else f"{point.y_error:.12g}"
    return (
        f"{point.candidate_id}/{point.variant_id}\n"
        f"backend={point.backend}; resource={point.resource or 'unspecified'}\n"
        f"precision={point.precision}; compensation={point.compensation}\n"
        f"latency={latency}; error={error}"
    )


def _category_order(values: set[str], mode: Literal["backend", "precision"]) -> list[str]:
    """Sort legend categories consistently.

    Args:
        values: Category labels present in the plot.
        mode: Backend categories for an overall plot, precision otherwise.

    Returns:
        Deterministically ordered category labels.

    """
    if mode == "precision":
        return sorted(values, key=lambda value: (_PRECISION_ORDER.get(value, 99), value))
    return sorted(values)


def _variant_shape_map(points: list[Measurement]) -> dict[str, str]:
    """Assign deterministic marker shapes to variants within one run.

    Args:
        points: Valid measurements whose variants need marker shapes.

    Returns:
        Mapping from variant identifier to SVG marker-shape name.

    """
    variants = sorted({point.variant_id for point in points})
    return {
        variant: _MARKER_SHAPES[index % len(_MARKER_SHAPES)]
        for index, variant in enumerate(variants)
    }


def _regular_polygon(sides: int, radius: float, rotation: float = -math.pi / 2) -> str:
    """Return SVG vertices for a regular polygon centered on the origin.

    Args:
        sides: Number of polygon vertices.
        radius: Distance from the origin to each vertex.
        rotation: Angular offset in radians.

    Returns:
        Space-separated SVG point coordinates.

    """
    return " ".join(
        f"{radius * math.cos(rotation + 2 * math.pi * index / sides):.2f},"
        f"{radius * math.sin(rotation + 2 * math.pi * index / sides):.2f}"
        for index in range(sides)
    )


def _star_points(radius: float) -> str:
    """Return SVG vertices for a five-point star centered on the origin.

    Args:
        radius: Outer radius of the star.

    Returns:
        Space-separated SVG point coordinates.

    """
    inner = radius * 0.45
    vertices: list[str] = []
    for index in range(10):
        point_radius = radius if index % 2 == 0 else inner
        angle = -math.pi / 2 + index * math.pi / 5
        vertices.append(
            f"{point_radius * math.cos(angle):.2f},{point_radius * math.sin(angle):.2f}"
        )
    return " ".join(vertices)


def _add_marker(
    parent: ET.Element,
    *,
    x: float,
    y: float,
    radius: float,
    shape: str,
    color: str,
    frontier: bool,
    variant_id: str,
    tooltip: str | None = None,
) -> ET.Element:
    """Add one shape-coded measurement marker to an SVG tree.

    Args:
        parent: SVG element receiving the marker group.
        x: Marker center x-coordinate.
        y: Marker center y-coordinate.
        radius: Marker size.
        shape: Shape name assigned to the variant.
        color: Fill color assigned to the backend or precision.
        frontier: Whether the marker belongs to the scoped frontier.
        variant_id: Variant identifier embedded as machine-readable metadata.
        tooltip: Optional exact provenance displayed on hover.

    Returns:
        SVG group containing the marker geometry.

    """
    group = ET.SubElement(
        parent,
        f"{{{_SVG}}}g",
        {
            "transform": f"translate({x:.2f} {y:.2f})",
            "data-frontier": str(frontier).lower(),
            "data-variant": variant_id,
            "data-shape": shape,
        },
    )
    if tooltip is not None:
        ET.SubElement(group, f"{{{_SVG}}}title").text = tooltip
    attributes = {
        "fill": color,
        "fill-opacity": "1" if frontier else "0.32",
        "stroke": "#202124" if frontier else color,
        "stroke-width": "2" if frontier else "1",
        "stroke-linejoin": "round",
    }
    if shape == "circle":
        ET.SubElement(group, f"{{{_SVG}}}circle", {"r": f"{radius:.2f}", **attributes})
    elif shape == "square":
        ET.SubElement(
            group,
            f"{{{_SVG}}}rect",
            {
                "x": f"{-radius:.2f}",
                "y": f"{-radius:.2f}",
                "width": f"{2 * radius:.2f}",
                "height": f"{2 * radius:.2f}",
                **attributes,
            },
        )
    elif shape == "diamond":
        ET.SubElement(
            group,
            f"{{{_SVG}}}polygon",
            {
                "points": f"0,{-radius:.2f} {radius:.2f},0 0,{radius:.2f} {-radius:.2f},0",
                **attributes,
            },
        )
    else:
        polygon = {
            "triangle-up": _regular_polygon(3, radius),
            "triangle-down": _regular_polygon(3, radius, math.pi / 2),
            "pentagon": _regular_polygon(5, radius),
            "hexagon": _regular_polygon(6, radius),
            "star": _star_points(radius),
        }.get(shape, _regular_polygon(6, radius))
        ET.SubElement(group, f"{{{_SVG}}}polygon", {"points": polygon, **attributes})
    return group


def render_pareto_svg(
    points: list[Measurement],
    *,
    title: str,
    category_mode: Literal["backend", "precision"],
    variant_shapes: dict[str, str] | None = None,
) -> str:
    """Render one self-contained latency/error Pareto plot as SVG.

    Args:
        points: Measurements in the desired global or per-backend scope.
        title: Plot title.
        category_mode: Color markers by backend or by precision.
        variant_shapes: Optional run-global variant-to-shape mapping.

    Returns:
        UTF-8 SVG document.

    """
    valid = _valid_measurements(points)
    frontier_ids = {id(point) for point in _frontier_points(valid)}
    effective_errors, zero_floor = _effective_errors(valid)
    shapes = variant_shapes or _variant_shape_map(valid)
    width, height = 1200, 720
    left, top, plot_width, plot_height = 112.0, 82.0, 790.0, 535.0
    root = ET.Element(
        f"{{{_SVG}}}svg",
        {
            "viewBox": f"0 0 {width} {height}",
            "width": str(width),
            "height": str(height),
            "role": "img",
            "aria-label": title,
        },
    )
    ET.SubElement(root, f"{{{_SVG}}}title").text = title
    ET.SubElement(root, f"{{{_SVG}}}style").text = """
        text { font-family: Inter, ui-sans-serif, system-ui, sans-serif; fill: #202124; }
        .title { font-size: 25px; font-weight: 650; }
        .subtitle { font-size: 13px; fill: #5f6368; }
        .axis { stroke: #202124; stroke-width: 1.4; }
        .grid { stroke: #dfe3e8; stroke-width: 1; }
        .tick { font-size: 12px; fill: #5f6368; }
        .axis-label { font-size: 15px; font-weight: 600; }
        .frontier-label { font-size: 11px; font-weight: 600; paint-order: stroke;
                          stroke: white; stroke-width: 3px; stroke-linejoin: round; }
        .legend { font-size: 13px; }
        .note { font-size: 12px; fill: #5f6368; }
    """
    ET.SubElement(root, f"{{{_SVG}}}rect", {"width": "1200", "height": "720", "fill": "white"})
    ET.SubElement(root, f"{{{_SVG}}}text", {"x": "42", "y": "38", "class": "title"}).text = title

    if not valid:
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {"x": "42", "y": "90", "class": "subtitle"},
        ).text = "No successful finite latency/error measurements were available."
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    subtitle = (
        f"{len(valid)} valid measurements · {len(frontier_ids)} frontier points · log–log axes"
    )
    if zero_floor is not None:
        subtitle += f" · exact zero shown at ≤ {_error_label(zero_floor)}"
    metric = valid[0].error_metric.replace("_", " ")
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": "42", "y": "62", "class": "subtitle"},
    ).text = subtitle

    x_low, x_high = _log_domain([_latency_value(point) for point in valid])
    y_low, y_high = _log_domain(list(effective_errors.values()))

    def x_position(value: float) -> float:
        return left + (math.log10(value) - x_low) / (x_high - x_low) * plot_width

    def y_position(value: float) -> float:
        return top + (y_high - math.log10(value)) / (y_high - y_low) * plot_height

    for tick in _log_ticks(x_low, x_high):
        x = x_position(tick)
        ET.SubElement(
            root,
            f"{{{_SVG}}}line",
            {
                "x1": f"{x:.2f}",
                "x2": f"{x:.2f}",
                "y1": str(top),
                "y2": str(top + plot_height),
                "class": "grid",
            },
        )
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {
                "x": f"{x:.2f}",
                "y": str(top + plot_height + 24),
                "text-anchor": "middle",
                "class": "tick",
            },
        ).text = _latency_label(tick)
    for tick in _log_ticks(y_low, y_high):
        y = y_position(tick)
        ET.SubElement(
            root,
            f"{{{_SVG}}}line",
            {
                "x1": str(left),
                "x2": str(left + plot_width),
                "y1": f"{y:.2f}",
                "y2": f"{y:.2f}",
                "class": "grid",
            },
        )
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {"x": str(left - 14), "y": f"{y + 4:.2f}", "text-anchor": "end", "class": "tick"},
        ).text = _error_label(tick)

    ET.SubElement(
        root,
        f"{{{_SVG}}}line",
        {
            "x1": str(left),
            "x2": str(left + plot_width),
            "y1": str(top + plot_height),
            "y2": str(top + plot_height),
            "class": "axis",
        },
    )
    ET.SubElement(
        root,
        f"{{{_SVG}}}line",
        {
            "x1": str(left),
            "x2": str(left),
            "y1": str(top),
            "y2": str(top + plot_height),
            "class": "axis",
        },
    )
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {
            "x": str(left + plot_width / 2),
            "y": "684",
            "text-anchor": "middle",
            "class": "axis-label",
        },
    ).text = "Median model-forward latency (lower is better)"
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {
            "x": "25",
            "y": str(top + plot_height / 2),
            "text-anchor": "middle",
            "transform": f"rotate(-90 25 {top + plot_height / 2})",
            "class": "axis-label",
        },
    ).text = f"{metric} (lower is better)"

    categories = _category_order(
        {point.backend if category_mode == "backend" else point.precision for point in valid},
        category_mode,
    )
    colors = {
        category: _PALETTE[index % len(_PALETTE)] for index, category in enumerate(categories)
    }
    plotted = [
        _PlotPoint(
            measurement=point,
            x=x_position(_latency_value(point)),
            y=y_position(effective_errors[id(point)]),
            frontier=id(point) in frontier_ids,
        )
        for point in valid
    ]
    frontier_plot = sorted(
        (point for point in plotted if point.frontier), key=lambda point: point.x
    )
    if len(frontier_plot) > 1:
        ET.SubElement(
            root,
            f"{{{_SVG}}}polyline",
            {
                "points": " ".join(f"{point.x:.2f},{point.y:.2f}" for point in frontier_plot),
                "fill": "none",
                "stroke": "#202124",
                "stroke-width": "2",
                "stroke-dasharray": "5 4",
                "opacity": "0.72",
            },
        )
    for plot_point in sorted(plotted, key=lambda point: point.frontier):
        point = plot_point.measurement
        category = point.backend if category_mode == "backend" else point.precision
        _add_marker(
            root,
            x=plot_point.x,
            y=plot_point.y,
            radius=7 if plot_point.frontier else 5,
            shape=shapes[point.variant_id],
            color=colors[category],
            frontier=plot_point.frontier,
            variant_id=point.variant_id,
            tooltip=_point_tooltip(point),
        )
        if plot_point.frontier:
            ET.SubElement(
                root,
                f"{{{_SVG}}}text",
                {
                    "x": f"{plot_point.x + 10:.2f}",
                    "y": f"{plot_point.y - 9:.2f}",
                    "class": "frontier-label",
                },
            ).text = _point_label(point)

    legend_x = 942
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": str(legend_x), "y": "108", "class": "axis-label"},
    ).text = "Backend" if category_mode == "backend" else "Precision"
    for index, category in enumerate(categories):
        y = 137 + index * 27
        ET.SubElement(
            root,
            f"{{{_SVG}}}circle",
            {"cx": str(legend_x + 7), "cy": str(y - 4), "r": "6", "fill": colors[category]},
        )
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {"x": str(legend_x + 23), "y": str(y), "class": "legend"},
        ).text = category
    variant_title_y = 178 + len(categories) * 27
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": str(legend_x), "y": str(variant_title_y), "class": "axis-label"},
    ).text = "Variant"
    visible_variants = sorted(shapes.items())[:9]
    for index, (variant_id, shape) in enumerate(visible_variants):
        y = variant_title_y + 28 + index * 25
        _add_marker(
            root,
            x=legend_x + 7,
            y=y - 4,
            radius=6,
            shape=shape,
            color="#5f6368",
            frontier=True,
            variant_id=variant_id,
        )
        label = variant_id if len(variant_id) <= 28 else variant_id[:27] + "…"
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {"x": str(legend_x + 23), "y": str(y), "class": "legend"},
        ).text = label
    overflow = len(shapes) - len(visible_variants)
    note_y = variant_title_y + 48 + len(visible_variants) * 25
    if overflow:
        ET.SubElement(
            root,
            f"{{{_SVG}}}text",
            {"x": str(legend_x), "y": str(note_y), "class": "note"},
        ).text = f"+ {overflow} additional variants"
        note_y += 24
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": str(legend_x), "y": str(note_y), "class": "note"},
    ).text = "Large outlined: frontier"
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": str(legend_x), "y": str(note_y + 21), "class": "note"},
    ).text = "Small translucent: dominated"
    ET.SubElement(
        root,
        f"{{{_SVG}}}text",
        {"x": str(legend_x), "y": str(note_y + 53), "class": "note"},
    ).text = "Hover markers for provenance"
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def write_pareto_visualizations(
    output_dir: Path,
    points: list[Measurement],
) -> dict[str, Any]:
    """Write overall and per-backend Pareto visualizations and exact data.

    Args:
        output_dir: Artifact directory dedicated to visualizations.
        points: All run measurements, including invalid and unsupported cells.

    Returns:
        JSON-serializable visualization manifest for embedding in ``run.json``.

    """
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = _valid_measurements(points)
    error_metrics = sorted({point.error_metric for point in valid})
    if len(error_metrics) > 1:
        raise ValueError(
            "Pareto visualization requires one shared error metric; found "
            + ", ".join(error_metrics)
        )
    error_metric = error_metrics[0] if error_metrics else "max_rel_error"
    variant_shapes = _variant_shape_map(valid)
    backends = sorted({point.backend for point in valid})
    slugs = _backend_slugs(backends)
    overall_frontier = _frontier_points(valid)
    overall_name = "pareto-overall.svg"
    atomic_write(
        output_dir / overall_name,
        render_pareto_svg(
            valid,
            title="Overall latency–error Pareto frontier",
            category_mode="backend",
            variant_shapes=variant_shapes,
        ),
    )
    devices: list[dict[str, Any]] = []
    device_frontiers: dict[str, list[dict[str, Any]]] = {}
    for backend in backends:
        scoped = [point for point in valid if point.backend == backend]
        frontier = _frontier_points(scoped)
        filename = f"pareto-{slugs[backend]}.svg"
        resources = sorted({point.resource for point in scoped if point.resource})
        atomic_write(
            output_dir / filename,
            render_pareto_svg(
                scoped,
                title=f"{backend} latency–error Pareto frontier",
                category_mode="precision",
                variant_shapes=variant_shapes,
            ),
        )
        device_frontiers[backend] = [point.to_dict() for point in frontier]
        devices.append(
            {
                "backend": backend,
                "resources": resources,
                "svg": f"visualizations/{filename}",
                "valid_points": len(scoped),
                "frontier_points": len(frontier),
            }
        )
    data = {
        "schema_version": 1,
        "overall": [point.to_dict() for point in overall_frontier],
        "devices": device_frontiers,
    }
    write_json(output_dir / "frontiers.json", data)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "axes": {
            "x": "median model-forward latency in seconds (log scale; lower is better)",
            "y": f"{error_metric} (log scale; lower is better)",
            "zero_error": "plotted at one decade below the smallest positive error",
        },
        "overall": {
            "svg": f"visualizations/{overall_name}",
            "valid_points": len(valid),
            "frontier_points": len(overall_frontier),
        },
        "devices": devices,
        "variant_markers": variant_shapes,
        "data": "visualizations/frontiers.json",
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest
