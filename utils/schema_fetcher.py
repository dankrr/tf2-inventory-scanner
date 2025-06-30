import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

SCHEMA: Dict[str, Any] | None = None
QUALITIES: Dict[str | int, str] = {}
PROPERTIES: Dict[str, Any] = {}

BASE_DIR = Path("cache")
FILES = {
    "schema": BASE_DIR / "schema.json",
    "defindexes": BASE_DIR / "defindexes.json",
    "qualities": BASE_DIR / "qualities.json",
    "killstreaks": BASE_DIR / "killstreaks.json",
    "effects": BASE_DIR / "effects.json",
    "paintkits": BASE_DIR / "paintkits.json",
    "wears": BASE_DIR / "wears.json",
    "crateseries": BASE_DIR / "crateseries.json",
    "paints": BASE_DIR / "paints.json",
    "strangeParts": BASE_DIR / "strangeParts.json",
    "craftWeapons": BASE_DIR / "craftWeapons.json",
    "uncraftWeapons": BASE_DIR / "uncraftWeapons.json",
    "itemGrade_v1": BASE_DIR / "itemGrade_v1.json",
    "itemGrade_v2": BASE_DIR / "itemGrade_v2.json",
}


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        logger.info("Missing enrichment file %s", path)
        return {}
    try:
        with path.open() as f:
            return json.load(f)
    except Exception as exc:  # pragma: no cover - corrupt file
        logger.info("Failed to load %s: %s", path, exc)
        return {}


def ensure_schema_cached() -> Dict[str, Any]:
    """Load schema and property files into memory."""

    global SCHEMA, QUALITIES, PROPERTIES
    if SCHEMA is not None:
        return SCHEMA

    SCHEMA = _load_json(FILES["defindexes"])
    QUALITIES = _load_json(FILES["qualities"])
    for key, path in FILES.items():
        if key in ("defindexes", "qualities"):
            continue
        PROPERTIES[key] = _load_json(path)
    logger.info("Loaded %s items from %s", len(SCHEMA), FILES["defindexes"])
    return SCHEMA
