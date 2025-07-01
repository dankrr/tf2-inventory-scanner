# convert_from_getplayeritems.py

import sys
import json
from uuid import uuid4

def convert_getplayeritems_to_community(input_file, output_file):
    with open(input_file) as f:
        data = json.load(f)

    if "items" not in data:
        print("❌ Error: No 'items' field found.")
        return

    converted = {"assets": [], "descriptions": []}

    for item in data["items"]:
        classid = str(item.get("defindex"))
        instanceid = str(item.get("id", uuid4().int & (1<<64)-1))  # fallback unique ID
        converted["assets"].append({
            "classid": classid,
            "instanceid": instanceid,
            "defindex": item.get("defindex"),
            "quality": item.get("quality"),
            "attributes": item.get("attributes", []),
            "tradable": item.get("tradable", 0),
            "marketable": item.get("marketable", 0)
        })

        converted["descriptions"].append({
            "classid": classid,
            "instanceid": instanceid,
            "app_data": {
                "def_index": classid,
                "quality": item.get("quality"),
                "attributes": item.get("attributes", []),
            },
            "tradable": item.get("tradable", 0),
            "marketable": item.get("marketable", 0),
        })

    with open(output_file, "w") as f:
        json.dump(converted, f, indent=2)

    print(f"✅ Converted {len(data['items'])} items → {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_from_getplayeritems.py <input.json> <output.json>")
        sys.exit(1)

    convert_getplayeritems_to_community(sys.argv[1], sys.argv[2])
