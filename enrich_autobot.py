import json
from pathlib import Path
import requests

BASE_URL = "https://schema.autobot.tf/properties/"
PROPS = {
    "effects": "effect_names.json",
    "paints": "paint_names.json",
    "wears": "wear_names.json",
    "killstreaks": "killstreak_names.json",
    "strangeParts": "strange_part_names.json",
    "paintkits": "paintkit_names.json",
    "crateseries": "crate_series_names.json",
}


def _invert_map(data: dict) -> dict:
    mapping = {}
    for k, v in data.items():
        if isinstance(k, str) and k.isdigit():
            mapping[k] = v
        elif isinstance(v, (int, str)) and str(v).isdigit():
            mapping[str(v)] = k
    return mapping


def fetch_all() -> None:
    cache = Path("cache")
    cache.mkdir(exist_ok=True)
    for endpoint, filename in PROPS.items():
        skip_invert = endpoint == "strangeParts"
        url = f"{BASE_URL}{endpoint}"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        data = r.json()
        mapping = data if skip_invert else _invert_map(data)
        (cache / filename).write_text(json.dumps(mapping))
        print(f"Fetched {len(mapping)} {endpoint} -> {cache/filename}")


if __name__ == "__main__":
    fetch_all()
