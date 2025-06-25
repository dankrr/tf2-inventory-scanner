import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

CACHE_PATH = Path(__file__).resolve().parents[1] / "data" / "schema.json"
TTL = 48 * 3600  # 48 hours


def get_schema():
    if CACHE_PATH.exists():
        age = time.time() - CACHE_PATH.stat().st_mtime
        if age < TTL:
            try:
                with open(CACHE_PATH) as f:
                    return json.load(f)
            except Exception:
                pass

    if not STEAM_API_KEY:
        return {}

    try:
        url = (
            "https://api.steampowered.com/IEconItems_440/GetSchemaURL/v1/?key="
            f"{STEAM_API_KEY}"
        )
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        schema_url = r.json()["result"].get("items_game_url")
        if not schema_url:
            return {}
        s = requests.get(schema_url, timeout=10)
        s.raise_for_status()
        data = s.json()
        CACHE_PATH.write_text(json.dumps(data))
        return data
    except Exception:
        if CACHE_PATH.exists():
            try:
                with open(CACHE_PATH) as f:
                    return json.load(f)
            except Exception:
                pass
    return {}
