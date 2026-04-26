"""Helpers for extracting TF2 item grade/tier metadata."""

from __future__ import annotations

from typing import Any, Dict, Iterable
import re


GRADE_COLOR_MAP: Dict[str, str] = {
    "Civilian Grade": "#9ED9FF",
    "Freelance Grade": "#5D8EFF",
    "Mercenary Grade": "#8C63FF",
    "Commando Grade": "#E65BFF",
    "Assassin Grade": "#FFA347",
    "Elite Grade": "#FF5E5E",
}

_GRADE_REGEX = re.compile(
    r"\b(Civilian Grade|Freelance Grade|Mercenary Grade|Commando Grade|Assassin Grade|Elite Grade)\b",
    re.IGNORECASE,
)


def _normalize_grade_name(raw: str | None) -> str | None:
    """Normalize a raw grade label to its canonical TF2 grade name."""

    if not raw:
        return None
    match = _GRADE_REGEX.search(raw)
    if not match:
        return None
    cleaned = match.group(1).strip().lower()
    for canonical in GRADE_COLOR_MAP:
        if canonical.lower() == cleaned:
            return canonical
    return None


def _iter_string_candidates(schema_entry: Dict[str, Any], asset: Dict[str, Any]) -> Iterable[str]:
    """Yield string fields that may contain a grade label."""

    for key in ("item_name", "name", "proper_name", "item_type_name"):
        val = schema_entry.get(key)
        if isinstance(val, str):
            yield val
    for key in ("custom_name", "custom_desc"):
        val = asset.get(key)
        if isinstance(val, str):
            yield val


def _extract_grade_tier(
    asset: Dict[str, Any],
    schema_entry: Dict[str, Any],
    display_name: str | None = None,
    resolved_name: str | None = None,
) -> Dict[str, str | None]:
    """Return normalized grade/tier fields for cosmetics, war paints, and skins.

    The extraction prefers schema-provided tag metadata and then falls back to
    parsing known grade labels from name-like fields.
    """

    grade_name: str | None = None

    tags = schema_entry.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if not isinstance(tag, dict):
                continue
            if str(tag.get("category", "")).lower() != "rarity":
                continue
            for key in ("localized_tag_name", "name", "internal_name"):
                parsed = _normalize_grade_name(tag.get(key))
                if parsed:
                    grade_name = parsed
                    break
            if grade_name:
                break

    if not grade_name:
        for text in (
            *list(_iter_string_candidates(schema_entry, asset)),
            display_name or "",
            resolved_name or "",
        ):
            parsed = _normalize_grade_name(text)
            if parsed:
                grade_name = parsed
                break

    color = GRADE_COLOR_MAP.get(grade_name or "")
    return {
        "grade": grade_name,
        "grade_name": grade_name,
        "grade_color": color,
        "tier": grade_name,
        "item_tier": grade_name,
        "item_tier_name": grade_name,
        "tier_color": color,
        "item_tier_color": color,
    }


__all__ = ["GRADE_COLOR_MAP", "_extract_grade_tier"]

