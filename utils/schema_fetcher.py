import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import requests

CACHE_FILE = Path("data/item_schema.json")
TTL = 48 * 60 * 60  # 48 hours


def ensure_schema_cached(api_key: str | None = None) -> Dict[str, Any]:
    """Return cached item schema mapping."""
    if api_key is None:
        api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise ValueError("STEAM_API_KEY is required to fetch item schema")

    global SCHEMA
    if CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < TTL:
            with CACHE_FILE.open() as f:
                schema = json.load(f)
            SCHEMA = schema
            print(f"Schema cache HIT ({len(schema)} items)")
            return schema

    url = "https://api.steampowered.com/IEconItems_440/GetSchema/v1/"
    r = requests.get(f"{url}?key={api_key}", timeout=20)
    r.raise_for_status()
    items = r.json().get("result", {}).get("items", [])
    schema = {str(item["defindex"]): item for item in items if "name" in item}
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w") as f:
        json.dump(schema, f)
    SCHEMA = schema
    print(f"Schema cache MISS (refetched {len(schema)} items)")
    return schema


# Module-level constant so other modules can import the schema without
# reloading the JSON file.
SCHEMA: Dict[str, Any] | None = None
