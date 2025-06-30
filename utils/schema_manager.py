import json
import logging
from pathlib import Path
from typing import Any, Dict

import vdf

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

    items_path = cache_dir / "schema_items.json"
    overview_path = cache_dir / "schema_overview.json"
    ig_path = cache_dir / "items_game.txt"

    items_map: Dict[str, Any] = {}
    data = _load_json(items_path)
    for item in data.get("result", {}).get("items", data.get("items", [])):
        idx = str(item.get("defindex"))
        if not idx:
            continue
        entry: Dict[str, Any] = {
            "defindex": item.get("defindex"),
            "name": item.get("name"),
        }
        if item.get("item_type_name"):
            entry["item_type_name"] = item["item_type_name"]
        path = (
            item.get("image_url_large")
            or item.get("image_url")
            or item.get("icon_url_large")
            or item.get("icon_url")
        )
        if path:
            entry["image_url"] = path
        items_map[idx] = entry

    overview = _load_json(overview_path).get("result", {})
    qualities = {str(v): k for k, v in overview.get("qualities", {}).items()}
    qualities_colored = overview.get("qualityNames", {})
    effects = overview.get("attribute_controlled_attached_particles", {})

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
        strange_parts = {
            str(idx): info.get("name")
            for idx, info in ig_raw.get("items", {}).items()
            if isinstance(info, dict) and info.get("item_class") == "strange_part"
        }

    hybrid = {
        "items": items_map,
        "attributes": ig_data.get("attributes", {}),
        "qualities": qualities,
        "qualities_colored": qualities_colored,
        "effects": effects,
        "paint_kits": ig_data.get("paint_kits", {}),
        "strange_parts": strange_parts,
    }

    for item in hybrid["items"].values():
        image = item.get("image_url") or item.get("image_url_large") or ""
        if isinstance(image, str) and image.startswith("http"):
            item["image"] = image
        elif image:
            item["image"] = f"https://steamcdn-a.akamaihd.net/{image.lstrip('/')}"
        else:
            item["image"] = ""
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
