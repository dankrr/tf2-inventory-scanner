import json
import logging
from pathlib import Path
from typing import Any, Dict

import vdf

ICON_BASE = "https://steamcdn-a.akamaihd.net/apps/440/icons/"

logger = logging.getLogger(__name__)

CACHE_DIR = Path("cache")
HYBRID_FILE = CACHE_DIR / "hybrid_schema.json"


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as f:
        try:
            return json.load(f)
        except Exception as exc:  # pragma: no cover - corrupt file
            logger.info("Failed to load %s: %s", path, exc)
            return {}


def build_hybrid_schema(cache_dir: Path = CACHE_DIR) -> Dict[str, Any]:
    """Merge schema data and items_game into a single mapping."""

    items_path = cache_dir / "defindexes.json"
    overview_path = cache_dir / "qualities.json"
    ig_path = cache_dir / "items_game.txt"

    items_map: Dict[str, Any] = {}
    data = _load_json(items_path)
    for idx, item in data.items():
        if not idx:
            continue
        if not isinstance(item, dict):
            continue
        entry: Dict[str, Any] = {"defindex": item.get("defindex", idx)}
        for key, value in item.items():
            entry[key] = value
        items_map[str(idx)] = entry

    qualities = _load_json(overview_path)
    qualities_colored = {}
    effects = _load_json(cache_dir / "effects.json")

    ig_data: Dict[str, Any] = {}
    strange_parts: Dict[str, Any] = {}
    if ig_path.exists():
        ig_raw = vdf.loads(ig_path.read_text()).get("items_game", {})
        ig_data = ig_raw
        for idx, meta in ig_raw.get("items", {}).items():
            if not isinstance(meta, dict):
                continue
            entry = items_map.setdefault(str(idx), {})
            for key, value in meta.items():
                entry.setdefault(key, value)
            if not entry.get("image"):
                icon_name = meta.get("image_inventory")
                if icon_name:
                    if not icon_name.endswith(".png"):
                        icon_name += ".png"
                    entry["image"] = ICON_BASE + icon_name.split("/")[-1]
        strange_parts = {
            str(idx): info.get("name")
            for idx, info in ig_raw.get("items", {}).items()
            if isinstance(info, dict) and info.get("item_class") == "strange_part"
        }

    paint_kits = _load_json(cache_dir / "paintkits.json")
    killstreakers = _load_json(cache_dir / "killstreaks.json")
    strange_parts.update(_load_json(cache_dir / "strangeParts.json"))

    hybrid = {
        "items": items_map,
        "attributes": ig_data.get("attributes", {}),
        "qualities": qualities,
        "qualities_colored": qualities_colored,
        "effects": effects,
        "paint_kits": paint_kits,
        "strange_parts": strange_parts,
        "killstreakers": killstreakers,
    }

    for item in items_map.values():
        if not item.get("image"):
            logger.warning(
                "Missing image for defindex %s (%s)",
                item.get("defindex"),
                item.get("name"),
            )

    cache_file = cache_dir / "hybrid_schema.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(hybrid))
    logger.info("Saved hybrid schema to %s", cache_file)
    return hybrid


def load_hybrid_schema(force_rebuild: bool = False) -> Dict[str, Any]:
    """Load cached hybrid schema, rebuilding if missing or forced."""

    path = HYBRID_FILE
    if path.exists() and not force_rebuild:
        with path.open() as f:
            data = json.load(f)
        if isinstance(data.get("items"), dict):
            return data

    return build_hybrid_schema(path.parent)
