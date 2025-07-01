import json
import sys

def convert_getplayeritems(raw):
    items = raw.get("result", {}).get("items", [])
    assets = []
    descriptions = []

    for item in items:
        defindex = str(item.get("defindex"))
        classid = defindex
        instanceid = "0"

        # Build asset
        asset = {
            "classid": classid,
            "instanceid": instanceid,
            "defindex": item.get("defindex"),
            "quality": item.get("quality"),
            "attributes": item.get("attributes", []),
        }
        assets.append(asset)

        # Build description
        descriptions.append({
            "classid": classid,
            "instanceid": instanceid,
            "tradable": int(item.get("flag_cannot_trade") != 1),
            "marketable": 0,  # Steam API doesn't expose this
            "app_data": {
                "def_index": defindex,
                "quality": str(item.get("quality", 6))
            }
        })

    return {
        "assets": assets,
        "descriptions": descriptions
    }

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_playeritems.py input.json output.json")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        raw = json.load(f)

    converted = convert_getplayeritems(raw)

    with open(sys.argv[2], "w") as out:
        json.dump(converted, out, indent=2)

    print(f"Converted {len(converted['assets'])} items.")
