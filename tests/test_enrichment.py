import json
import os
from pathlib import Path

import pytest

from utils.inventory_processor import enrich_inventory

TEST_STEAM_ID = os.getenv("TEST_STEAM_ID")
INV_PATH = Path("cache") / f"inventory_{TEST_STEAM_ID}.json"


@pytest.mark.skipif(not INV_PATH.exists(), reason="cache not populated")
def test_enrichment_end_to_end():
    with INV_PATH.open() as f:
        data = json.load(f)
    items = enrich_inventory(data)
    assert items

    required = {
        "defindex",
        "name",
        "base_name",
        "quality",
        "quality_color",
        "origin",
        "image_url",
        "level",
        "paint_name",
        "paint_hex",
        "spells",
        "spell_flags",
        "killstreak_tier",
        "sheen",
        "killstreaker",
        "strange_parts",
        "unusual_effect",
        "is_festivized",
        "badges",
        "misc_attrs",
    }
    assert any(required <= item.keys() for item in items)

    badge_ratio = sum(1 for i in items if i.get("badges")) / len(items)
    assert badge_ratio >= 0.9

    assert not any(i["name"].startswith("Unknown") for i in items)

    target = None
    for it in items:
        flags = it.get("spell_flags", {})
        if flags.get("footprints") and flags.get("pumpkin_bombs"):
            target = it
            break
    assert target is not None
    assert "Fire Footprints" in target.get("spells", [])
    assert "Pumpkin Bombs" in target.get("spells", [])
