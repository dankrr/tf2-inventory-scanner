
import json
from pathlib import Path


QUALITY_COLORS = {
    0: "#B2B2B2",
    1: "#4D7455",
    3: "#476291",
    5: "#8650AC",
    6: "#FFD700",
    11: "#CF6A32",
    13: "#FAFAFA",
}

PLACEHOLDER_IMG = "https://via.placeholder.com/64"

# Load a small item schema mapping if available
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "data" / "item_schema.json"
try:
    with open(SCHEMA_PATH) as f:
        ITEM_SCHEMA = json.load(f)
except FileNotFoundError:
    ITEM_SCHEMA = {}


def get_item_name(defindex: int) -> str:
    """Return human readable name for defindex."""
    return ITEM_SCHEMA.get(str(defindex), f"Item {defindex}")


def process_inventory(items):
    processed = []
    for i in items:
        icon = i.get("icon_url")
        image_url = (
            f"https://steamcommunity-a.akamaihd.net/economy/image/{icon}"
            if icon else PLACEHOLDER_IMG
        )
        processed.append(
            {
                "name": get_item_name(i["defindex"]),
                "image_url": image_url,
                "quality": i.get("quality", 6),
            }
        )
    return processed
