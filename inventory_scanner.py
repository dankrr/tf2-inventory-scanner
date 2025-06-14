import requests
import sys

API_URL_TEMPLATE = "https://steamcommunity.com/inventory/{steamid}/440/2?l=english&count=5000"


def fetch_inventory(steamid: str) -> dict:
    """Fetch a user's TF2 inventory from the Steam Community API."""
    url = API_URL_TEMPLATE.format(steamid=steamid)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Failed to fetch inventory: {exc}")
        return {}
    return response.json()


def main(args: list[str]) -> None:
    if not args:
        print("Usage: python inventory_scanner.py <steamid>")
        sys.exit(1)

    steamid = args[0]
    data = fetch_inventory(steamid)
    items = data.get("assets", [])
    print(f"Found {len(items)} items in inventory for {steamid}")

    # Optionally, print item names if available
    descriptions = {d["classid"]: d for d in data.get("descriptions", [])}
    for item in items:
        classid = item.get("classid")
        desc = descriptions.get(classid)
        name = desc.get("market_hash_name") if desc else "Unknown Item"
        print(f"- {name}")


if __name__ == "__main__":
    main(sys.argv[1:])
