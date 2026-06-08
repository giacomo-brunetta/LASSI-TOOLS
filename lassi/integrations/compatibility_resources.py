from __future__ import annotations

import json
from pathlib import Path


SERVER_ROOT = Path(__file__).resolve().parents[2]
COMPAT_RESOURCE_ROOT = SERVER_ROOT / "resources" / "compatibility"
COMPAT_DB_PATH = COMPAT_RESOURCE_ROOT / "compat_db.json"
COMPAT_WIKI_DIR = COMPAT_RESOURCE_ROOT / "wiki"


def load_compat_database() -> dict:
    if not COMPAT_DB_PATH.exists():
        return {}
    with COMPAT_DB_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonicalize_compat_op_name(raw_name: str, database: dict) -> str | None:
    if not raw_name:
        return None

    name = raw_name.strip()
    if name in database:
        return name

    candidates = []
    lowered = name.lower()

    if not lowered.startswith("aten."):
        candidates.append(f"aten.{name}")

    if lowered.startswith("torch.nn.functional."):
        base = name.split(".")[-1]
        candidates.extend([f"aten.{base}.int", f"aten.{base}"])

    if lowered.startswith("torch."):
        suffix = name.split(".", maxsplit=1)[1]
        candidates.extend([f"aten.{suffix}", f"aten.{suffix}.int"])

    base = name.split(".")[-1]
    candidates.extend([f"aten.{base}.int", f"aten.{base}"])

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate in database:
            return candidate

    return None


def wiki_resource_help() -> str:
    database = load_compat_database()
    return json.dumps(
        {
            "name": "LASSI Compatibility Wiki Resources",
            "canonical_resources": [
                "wiki://help",
                "wiki://compatibility/index",
                "wiki://compatibility/op/{name}",
                "wiki://compatibility/search/{pattern}",
            ],
            "aliases": [
                "wiki://compatibility",
                "wiki://compatibility/function/{name}",
                "wiki://compatibility/torch/{name}",
            ],
            "name_normalization_examples": [
                {"input": "torch.matmul", "canonical": "aten.matmul"},
                {"input": "torch.nn.functional.softmax", "canonical": "aten.softmax.int (if present)"},
                {"input": "softmax", "canonical": "aten.softmax.int or aten.softmax"},
            ],
            "quickstart": [
                "1) Query wiki://compatibility/index",
                "2) Query wiki://compatibility/search/<term>",
                "3) Query wiki://compatibility/op/<op_name>",
            ],
            "database_available": bool(database),
            "total_ops": len(database),
        },
        indent=2,
    )


def compatibility_wiki_index() -> str:
    if not COMPAT_DB_PATH.exists():
        return f"Compatibility database not found at {COMPAT_DB_PATH}"

    database = load_compat_database()
    supported = sorted(op_name for op_name, info in database.items() if info.get("supported"))
    unsupported = sorted(op_name for op_name, info in database.items() if not info.get("supported"))

    return json.dumps(
        {
            "database_path": str(COMPAT_DB_PATH),
            "wiki_dir": str(COMPAT_WIKI_DIR),
            "help_uri": "wiki://help",
            "resource_templates": [
                "wiki://compatibility/index",
                "wiki://compatibility/op/{name}",
                "wiki://compatibility/search/{pattern}",
            ],
            "total_ops": len(database),
            "supported_count": len(supported),
            "unsupported_count": len(unsupported),
            "sample_supported": supported[:25],
            "sample_unsupported": unsupported[:25],
        },
        indent=2,
    )


def compatibility_wiki_entry(name: str) -> str:
    if not COMPAT_WIKI_DIR.exists():
        return f"Compatibility wiki directory not found at {COMPAT_WIKI_DIR}"

    database = load_compat_database()
    canonical = canonicalize_compat_op_name(name, database) or name

    page_path = COMPAT_WIKI_DIR / f"{canonical}.md"
    if page_path.exists():
        return page_path.read_text(encoding="utf-8")

    if database and canonical in database:
        info = database[canonical]
        status = "Supported" if info.get("supported") else "Unsupported"
        error = info.get("error") or "None"
        return (
            f"# {canonical}\n\n"
            f"- Query Input: {name}\n"
            f"- Status: {status}\n"
            f"- Error: {error}\n"
        )

    suggestions = []
    lowered = name.lower().strip()
    for op_name in sorted(database.keys()):
        if lowered and lowered in op_name.lower():
            suggestions.append(op_name)
        if len(suggestions) >= 10:
            break

    return json.dumps(
        {
            "error": f"No compatibility wiki entry found for op: {name}",
            "help_uri": "wiki://help",
            "try_search_uri": f"wiki://compatibility/search/{name}",
            "valid_template": "wiki://compatibility/op/{name}",
            "normalized_candidate": canonicalize_compat_op_name(name, database),
            "suggestions": suggestions,
        },
        indent=2,
    )


def search_compatibility_wiki(pattern: str) -> str:
    if not COMPAT_DB_PATH.exists():
        return f"Compatibility database not found at {COMPAT_DB_PATH}"

    database = load_compat_database()
    support_filter = None
    needle = pattern.strip()
    lowered = needle.lower()

    if lowered.startswith("supported:"):
        support_filter = True
        needle = needle.split(":", maxsplit=1)[1].strip()
    elif lowered.startswith("unsupported:"):
        support_filter = False
        needle = needle.split(":", maxsplit=1)[1].strip()

    matches = []
    normalized_candidate = canonicalize_compat_op_name(needle, database)
    needle_lower = needle.lower()
    for op_name, info in sorted(database.items()):
        if needle_lower and needle_lower not in op_name.lower():
            continue
        if support_filter is not None and bool(info.get("supported")) is not support_filter:
            continue
        matches.append(
            {
                "op_name": op_name,
                "supported": bool(info.get("supported")),
                "error": info.get("error"),
                "uri": f"wiki://compatibility/op/{op_name}",
            }
        )

    if not matches and normalized_candidate and normalized_candidate in database:
        info = database[normalized_candidate]
        matches.append(
            {
                "op_name": normalized_candidate,
                "supported": bool(info.get("supported")),
                "error": info.get("error"),
                "uri": f"wiki://compatibility/op/{normalized_candidate}",
                "normalized_from": pattern,
            }
        )

    return json.dumps(
        {
            "pattern": pattern,
            "normalized_candidate": normalized_candidate,
            "help_uri": "wiki://help",
            "match_count": len(matches),
            "matches": matches[:100],
        },
        indent=2,
    )
