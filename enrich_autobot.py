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
    endpoints = list(PROPS.items())
    for name, filename in endpoints:
        # Use override for strangeParts
        if name == "strangeParts":
            url = f"https://schema.autobot.tf/properties/{name}"
        else:
            url = f"https://schema.autobot.tf/{name}"

        try:
            resp = requests.get(url, headers={"accept": "*/*"})
            resp.raise_for_status()
            data = resp.json()
            dest = Path("cache") / filename
            dest.write_text(json.dumps(data, indent=2))
            print(f"Fetched {len(data)} {name} -> {dest}")
        except Exception as e:
            print(f"\N{WARNING SIGN} Failed to fetch {name}: {e}")


if __name__ == "__main__":
    fetch_all()
