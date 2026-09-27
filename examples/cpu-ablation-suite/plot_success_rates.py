"""Rebuild the recorded CPU campaign comparison as a dependency-free SVG."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = {
    "Terra": "runs/cpu-model-comparison-medium-20260916/terra",
    "Luna": "runs/cpu-model-comparison-medium-20260916/luna",
    "DS4 Flash": "runs/cpu-deepseek-v4-flash-20260918",
}


def collect() -> dict:
    result = {}
    for model, relative in CAMPAIGNS.items():
        root = ROOT / relative
        entries = json.loads((root / "suite.json").read_text())["entries"]
        selected = {}
        for entry in entries:
            for path in sorted((root / "runs" / entry["name"]).glob("*/run.json")):
                raw = path.read_text()
                record = json.loads(raw)
                # Infrastructure interruptions are not numerical validation outcomes.
                if record.get("accuracy") and "usage limit has been reached" not in raw.lower():
                    selected[entry["name"]] = (path, record)
        metrics = [record["accuracy"] for _, record in selected.values()]
        result[model] = {
            "planned_kernels": len(entries),
            "evaluated_kernels": len(selected),
            "solved_kernels": sum(m["kernel_solved"] for m in metrics),
            **{
                key: sum(m[key] for m in metrics)
                for key in ("samples", "initial_passes", "final_passes", "recovered_by_repair")
            },
            "sources": [str(path.relative_to(ROOT)) for path, _ in selected.values()],
        }
    return result


def render(data: dict, timestamp: str) -> str:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1380" height="680" viewBox="0 0 1380 680">',
        '<rect width="1380" height="680" fill="#f5f7fb"/>',
        "<style>text{font-family:Arial,Helvetica,sans-serif;fill:#203047}.muted{fill:#627088}</style>",
    ]

    def label(x, y, text, size=16, **attrs):
        attributes = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {attributes}>{escape(text)}</text>')

    label(44, 53, "CPU verification: model success rates", 30, font_weight=700)
    label(
        44,
        84,
        "PolyBench + scientific kernels · MINI inputs · medium effort · up to 2 correction rounds",
        17,
        class_="muted",
    )
    panels = [
        ("First-attempt candidates", "initial_passes", "samples"),
        ("Final candidates", "final_passes", "samples"),
        ("Kernels solved", "solved_kernels", "evaluated_kernels"),
    ]
    colors = {"Terra": "#3478c5", "Luna": "#8157bb", "DS4 Flash": "#d68624"}
    for i, (title, numerator, denominator) in enumerate(panels):
        x = 44 + i * 442
        parts.append(f'<rect x="{x}" y="118" width="410" height="352" rx="16" fill="white"/>')
        label(x + 22, 154, title, 21, font_weight=700)
        label(x + 22, 179, "Among evaluated results only", 14, class_="muted")
        for j, (model, counts) in enumerate(data.items()):
            y = 218 + j * 78
            n, d = counts[numerator], counts[denominator]
            rate = n / d if d else 0
            label(x + 22, y, model, 16, font_weight=600)
            label(x + 388, y, f"{100 * rate:.1f}% · {n}/{d}", 16, text_anchor="end")
            parts.append(
                f'<rect x="{x + 22}" y="{y + 12}" width="366" height="18" rx="6" fill="#e9edf4"/>'
            )
            parts.append(
                f'<rect x="{x + 22}" y="{y + 12}" width="{366 * rate:.2f}" '
                f'height="18" rx="6" fill="{colors[model]}"/>'
            )
    label(44, 511, "Evaluated coverage", 19, font_weight=700)
    for i, (model, counts) in enumerate(data.items()):
        label(
            44 + i * 442,
            543,
            f"{model}: {counts['evaluated_kernels']}/{counts['planned_kernels']} kernels",
            19,
        )
    label(
        44,
        585,
        "DS4 is preliminary: only correlation, covariance and GEMM have completed evaluation.",
        17,
        font_weight=600,
    )
    label(
        44,
        611,
        "Unevaluated kernels / connection and quota interruptions "
        "are not counted as model validation failures.",
        16,
        class_="muted",
    )
    label(
        44,
        639,
        "Latest completed non-quota result per kernel; discarded campaign excluded. "
        "Accelerator compatibility is not measured here.",
        14,
        class_="muted",
    )
    label(
        44,
        662,
        f"Snapshot: {timestamp} · Descriptive arena rates, not IID pass@k estimates.",
        13,
        class_="muted",
    )
    parts.append("</svg>")
    # Python identifiers use class_; SVG uses class.
    return "\n".join(parts).replace("class-=", "class=")


if __name__ == "__main__":
    data = collect()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    output = ROOT / "docs" / "experiments" / "figures"
    output.mkdir(parents=True, exist_ok=True)
    (output / "cpu-model-success-rates.svg").write_text(render(data, timestamp))
    (output / "cpu-model-success-rates.json").write_text(
        json.dumps(
            {
                "snapshot_utc": timestamp,
                "models": data,
                "selection": (
                    "Latest result per kernel with accuracy metrics, excluding quota interruptions."
                ),
            },
            indent=2,
        )
        + "\n"
    )
    for model, counts in data.items():
        print(model, {key: value for key, value in counts.items() if key != "sources"})
