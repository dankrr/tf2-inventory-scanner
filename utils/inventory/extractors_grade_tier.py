"""Helpers for extracting TF2 item grade metadata while keeping killstreak tiers separate."""

from __future__ import annotations

from typing import Any, Dict, Iterable
import re

from .. import local_data
from ..schema_provider import SchemaProvider


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

_GRADE_ENDPOINT_LOOKUPS: dict[int, str | None] = {}
_GRADE_PROVIDER: SchemaProvider | None = None


def short_grade_label(grade_name: str | None) -> str | None:
    """Return a display-safe short label for a canonical grade name.

    Examples:
        ``"Commando Grade" -> "Commando"``
        ``"Elite Grade" -> "Elite"``
    """

    if not grade_name:
        return None
    normalized = _normalize_grade_name(grade_name) or grade_name.strip()
    return re.sub(r"\s+Grade$", "", normalized, flags=re.IGNORECASE).strip()


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


def _extract_grade_from_tags(asset: Dict[str, Any], schema_entry: Dict[str, Any]) -> str | None:
    """Resolve grade name from Steam Econ tags first, then schema tags."""

    for tag_source in (asset.get("tags"), schema_entry.get("tags")):
        if not isinstance(tag_source, list):
            continue
        for tag in tag_source:
            if not isinstance(tag, dict):
                continue
            category = str(tag.get("category", "")).lower()
            category_name = str(tag.get("category_name", "")).lower()
            if category != "rarity" and category_name != "grade":
                continue
            for key in ("localized_tag_name", "name", "internal_name"):
                parsed = _normalize_grade_name(tag.get(key))
                if parsed:
                    return parsed
    return None


def _grade_provider() -> SchemaProvider:
    """Return a singleton schema provider used for grade endpoint fallback."""

    global _GRADE_PROVIDER
    if _GRADE_PROVIDER is None:
        _GRADE_PROVIDER = SchemaProvider(cache_dir=local_data.ITEM_GRADE_FILE.parent)
    return _GRADE_PROVIDER


def _resolve_grade_from_defindex(defindex: int | None) -> tuple[str | None, str]:
    """Resolve grade from cached v2 map and defindex endpoint fallback."""

    if defindex is None:
        return None, "none"

    cached = local_data.ITEM_GRADE_BY_DEFINDEX.get(int(defindex))
    normalized = _normalize_grade_name(cached)
    if normalized:
        return normalized, "schema_grade_v2"

    if int(defindex) in _GRADE_ENDPOINT_LOOKUPS:
        normalized = _normalize_grade_name(_GRADE_ENDPOINT_LOOKUPS[int(defindex)])
        return normalized, "grade_endpoint" if normalized else "none"

    fetched = _grade_provider().get_item_grade_from_defindex(int(defindex))
    _GRADE_ENDPOINT_LOOKUPS[int(defindex)] = fetched
    normalized = _normalize_grade_name(fetched)
    if normalized:
        return normalized, "grade_endpoint"
    return None, "none"


def _extract_grade_tier(
    asset: Dict[str, Any],
    schema_entry: Dict[str, Any],
    display_name: str | None = None,
    resolved_name: str | None = None,
    defindex: int | None = None,
) -> Dict[str, str | None]:
    """Return normalized grade fields; never aliases killstreak tiers into grade."""

    grade_name = _extract_grade_from_tags(asset, schema_entry)
    grade_source = "econ_tag" if grade_name else "none"

    if not grade_name:
        grade_name, grade_source = _resolve_grade_from_defindex(defindex)

    if not grade_name:
        for text in (
            *list(_iter_string_candidates(schema_entry, asset)),
            display_name or "",
            resolved_name or "",
        ):
            parsed = _normalize_grade_name(text)
            if parsed:
                grade_name = parsed
                grade_source = "name_fallback"
                break

    color = GRADE_COLOR_MAP.get(grade_name or "")
    grade_slug = (grade_name or "").lower().replace(" ", "-") if grade_name else None
    grade_short_name = short_grade_label(grade_name)
    return {
        "grade": grade_name,
        "grade_name": grade_name,
        "grade_short_name": grade_short_name,
        "grade_color": color,
        "grade_slug": grade_slug,
        "tier": grade_name,
        "item_tier": grade_name,
        "item_tier_name": grade_name,
        "tier_color": color,
        "item_tier_color": color,
        "grade_source": grade_source if grade_name else "none",
    }


__all__ = ["GRADE_COLOR_MAP", "short_grade_label", "_extract_grade_tier"]
