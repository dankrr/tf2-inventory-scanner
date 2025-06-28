import os

from services import pricing_service
from utils.cache_manager import read_json, write_json


def main() -> None:
    api_key = os.getenv("BACKPACK_API_KEY")
    if not api_key:
        raise ValueError("BACKPACK_API_KEY is required")

    current = read_json(pricing_service.PRICE_CACHE_FILE)
    fetched = pricing_service._fetch_prices(api_key)
    updated = False
    for sku, entry in fetched.items():
        if current.get(sku, {}).get("last_update") != entry.get("last_update"):
            current[sku] = entry
            updated = True
    if updated:
        write_json(pricing_service.PRICE_CACHE_FILE, current)

    currencies = pricing_service._fetch_currencies(api_key)
    if currencies:
        write_json(pricing_service.CURRENCY_FILE, currencies)


if __name__ == "__main__":
    main()
