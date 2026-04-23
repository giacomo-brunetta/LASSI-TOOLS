"""Generate markdown wiki pages from the compatibility database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from compat_tool.utils import ensure_directory


def generate_markdown(db: dict[str, dict[str, Any]], output_dir: str) -> None:
    """Write one markdown file per op into `output_dir`."""
    target_dir = ensure_directory(output_dir)

    for op_name, info in sorted(db.items()):
        status = "✅ Supported" if info.get("supported") else "❌ Unsupported"
        error = info.get("error") or "None"
        lines = [
            f"# {op_name}",
            "",
            f"- Status: {status}",
            f"- Error: {error}",
        ]

        supported_profiles = info.get("supported_profiles") or []
        if supported_profiles:
            lines.append(f"- Supported Profiles: {', '.join(supported_profiles)}")

        for note in info.get("dtype_notes") or []:
            lines.append(f"- DType Note: {note}")

        if info.get("range_restriction"):
            lines.append(f"- Range Restriction: {info['range_restriction']}")

        if info.get("recommended_alternative"):
            lines.append(f"- Alternative: Use `{info['recommended_alternative']}` instead of this.")

        attempts = info.get("attempts") or {}
        if attempts:
            lines.extend(["", "## Attempts", ""])
            for profile_name, attempt in sorted(attempts.items()):
                attempt_status = "supported" if attempt.get("supported") else "unsupported"
                attempt_error = attempt.get("error") or "None"
                lines.append(f"- `{profile_name}`: {attempt_status}; dtype={attempt.get('dtype')}; error={attempt_error}")
                if attempt.get("input_spec"):
                    lines.append(f"  spec={attempt['input_spec']}")
                if attempt.get("range_note"):
                    lines.append(f"  note={attempt['range_note']}")

        lines.append("")
        content = "\n".join(lines)
        (Path(target_dir) / f"{op_name}.md").write_text(content, encoding="utf-8")
