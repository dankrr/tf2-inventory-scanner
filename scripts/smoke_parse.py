import json
from pathlib import Path
import sys

from utils import schema_manager, inventory_processor


def main() -> None:
    inv_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("inventory.json")
    if not inv_file.exists():
        print(f"Missing {inv_file}")
        return
    data = json.loads(inv_file.read_text())
    schema_manager.load_hybrid_schema()
    items = inventory_processor.enrich_inventory(data)
    for item in items:
        badges = "".join(item.get("badges", []))
        print(f"{item['name']}: {badges}")


if __name__ == "__main__":
    main()
