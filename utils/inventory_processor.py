
import json
from pathlib import Path

from utils.schema_fetcher import get_schema


QUALITY_COLORS = {
    0: "#B2B2B2",
    1: "#4D7455",
    3: "#476291",
    5: "#8650AC",
    6: "#FFD700",
    11: "#CF6A32",
    13: "#FAFAFA",
}

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "item_schema.json"
try:
    with open(SCHEMA_PATH) as f:
        FALLBACK_SCHEMA = json.load(f)
except FileNotFoundError:
    FALLBACK_SCHEMA = {}

SCHEMA = get_schema() or FALLBACK_SCHEMA


def get_item_name(defindex: int) -> str:
    """Return human readable name for defindex."""
    return SCHEMA.get(str(defindex), f"Item {defindex}")


def _img(icon: str) -> str:
    if not icon:
        return ""
    return f"https://steamcommunity-a.akamaihd.net/economy/image/{icon}"


def process_inventory(items):
    processed = []
    for i in items[:50]:
        processed.append(
            {
                "name": get_item_name(i["defindex"]),
                "image_url": _img(i.get("icon_url")),
                "quality": i.get("quality", 6),
            }
        )
    return processed
