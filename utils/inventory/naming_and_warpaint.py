from typing import Dict, Any, List

from .extractors_unusual_killstreak import _extract_killstreak


def _build_item_name(base: str, quality: str, asset: Dict[str, Any]) -> str:
    """Return the display name prefixed with quality and killstreak info."""

    parts: List[str] = []
    ks_tier, sheen, _ = _extract_killstreak(asset)

    if ks_tier:
        parts.append(ks_tier)

    if quality not in ("Unique", "Normal"):
        parts.append(quality)

    parts.append(base)

    if sheen:
        parts.append(f"({sheen})")

    return " ".join(parts)


def _is_placeholder_name(name: str) -> bool:
    """Return True if ``name`` looks like an internal placeholder."""

    lname = name.lower()
    if "tf_" in lname or "tf-" in lname or "weapon" in lname and " " not in name:
        return True
    if "_" in name:
        return True
    if lname in {"rifle", "smg", "pistol", "shotgun", "decoder ring"}:
        return True
    if name.isupper():
        return True
    return False


def _preferred_base_name(defindex: str, schema_entry: Dict[str, Any]) -> str:
    """Return human readable base item name."""

    name = schema_entry.get("item_name") or schema_entry.get("name")
    if name and not _is_placeholder_name(name):
        return name

    return name or f"Item #{defindex}"


def _is_warpaintable(schema_entry: Dict[str, Any]) -> bool:
    """Return True if ``schema_entry`` represents a weapon that can be warpainted."""

    if (
        schema_entry.get("craft_class") != "weapon"
        and schema_entry.get("craft_material_type") != "weapon"
    ):
        item_class = schema_entry.get("item_class", "")
        if not item_class.startswith("tf_weapon_"):
            return False

    name = schema_entry.get("item_name") or schema_entry.get("name") or ""
    if _is_placeholder_name(name):
        return False

    return True


__all__ = [
    "_build_item_name",
    "_is_placeholder_name",
    "_preferred_base_name",
    "_is_warpaintable",
]
