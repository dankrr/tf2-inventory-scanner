import os
import requests
import sys

API_URL_TEMPLATE = (
    "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v0001/"
    "?key={key}&steamid={steamid}"
)


def fetch_inventory(steamid: str) -> dict:
    """Fetch a user's TF2 inventory via the Steam Web API."""
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise ValueError("STEAM_API_KEY is required")
    url = API_URL_TEMPLATE.format(key=api_key, steamid=steamid)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch inventory: {exc}")
        return {}
    return response.json().get("result", {})


def main(args: list[str]) -> None:
    if not args:
        print("Usage: python inventory_scanner.py <steamid>")
        sys.exit(1)

    steamid = args[0]
    data = fetch_inventory(steamid)
    items = data.get("items", [])
    print(f"Found {len(items)} items in inventory for {steamid}")

    for item in items:
        defindex = item.get("defindex")
        quality = item.get("quality")
        print(f"- defindex={defindex} quality={quality}")


if __name__ == "__main__":
    main(sys.argv[1:])
