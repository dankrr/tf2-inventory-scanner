import json
from utils.inventory_processor import enrich_inventory

for path in [
    "tests/fixtures/pro_item.json",
    "tests/fixtures/simple_item.json",
    "tests/fixtures/unusual_item.json",
]:
    with open(path) as f:
        data = {"items": [json.load(f)]}
        items = enrich_inventory(data)
        badges = sum(len(i.get("badges", [])) for i in items)
        print(f"{path}: {len(items)} items, {badges} badges")

print("OK")
