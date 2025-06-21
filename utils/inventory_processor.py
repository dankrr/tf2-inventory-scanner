
QUALITY_COLORS = {
    0: "#B2B2B2",
    1: "#4D7455",
    3: "#476291",
    5: "#8650AC",
    6: "#FFD700",
    11: "#CF6A32",
    13: "#FAFAFA"
}

def process_inventory(items):
    return [
        {
            "name": f"Item {i['defindex']}",
            "image_url": f"https://steamcommunity-a.akamaihd.net/economy/image/{i.get('icon_url', '')}",
            "quality": i.get("quality", 6)
        }
        for i in items
    ]
