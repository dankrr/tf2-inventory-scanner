from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

# Paths to cached schema files
SCHEMA_FILE = Path(os.getenv("TF2_SCHEMA_FILE", "cache/tf2_schema.json"))
ITEMS_GAME_FILE = Path(
    os.getenv("TF2_ITEMS_GAME_FILE", "cache/items_game_cleaned.json")
)


def _load(path: Path) -> Dict[str, Any]:
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return {}


_schema = _load(SCHEMA_FILE)
_ig = _load(ITEMS_GAME_FILE)

TF2_SCHEMA: Dict[str, Any] = _schema.get("items", _schema)
ITEMS_GAME_CLEANED: Dict[str, Any] = _ig
EFFECT_NAMES: Dict[str, str] = _schema.get("effects", {})

# Build lookup tables -------------------------------------------------------

_colors = _schema.get("qualityColors", {})
QUALITY_MAP: Dict[int, Dict[str, str]] = {}
for name, qid in (_schema.get("qualities") or {}).items():
    qid_int = int(qid)
    color = _colors.get(str(qid_int)) or _colors.get(str(name).lower()) or "#B2B2B2"
    QUALITY_MAP[qid_int] = {"name": str(name), "hex": str(color)}

ORIGIN_MAP: Dict[int, str] = {
    int(entry.get("origin", 0)): str(entry.get("name", ""))
    for entry in (_schema.get("originNames") or [])
    if isinstance(entry, dict)
}

PAINTS: Dict[int, Dict[str, str]] = {
    int(k): {"name": str(v.get("name", "")), "hex": str(v.get("hex", ""))}
    for k, v in (_ig.get("paints") or {}).items()
    if isinstance(v, dict)
}
if not PAINTS:
    PAINTS = {
        3100495: {"name": "A Color Similar to Slate", "hex": "#2F4F4F"},
        8208497: {"name": "A Deep Commitment to Purple", "hex": "#7D4071"},
        8208498: {"name": "A Distinctive Lack of Hue", "hex": "#141414"},
        1315860: {"name": "An Extraordinary Abundance of Tinge", "hex": "#CF7336"},
        2960676: {"name": "Color No. 216-190-216", "hex": "#D8BED8"},
        8289918: {"name": "Dark Salmon Injustice", "hex": "#8847FF"},
        15132390: {"name": "Drably Olive", "hex": "#808000"},
        8421376: {"name": "Indubitably Green", "hex": "#729E42"},
        13595446: {"name": "Mann Co. Orange", "hex": "#CF7336"},
        12377523: {"name": "Muskelmannbraun", "hex": "#A57545"},
        5322826: {"name": "Noble Hatter's Violet", "hex": "#51384A"},
        15787660: {"name": "Pink as Hell", "hex": "#FF69B4"},
        15185211: {"name": "A Mann's Mint", "hex": "#BCDDB3"},
    }

SHEENS: Dict[int, str] = {
    int(k): str(v) for k, v in (_ig.get("sheens") or {}).items() if isinstance(v, str)
}
if not SHEENS:
    SHEENS = {
        1: "Team Shine",
        2: "Deadly Daffodil",
        3: "Mandarin",
        4: "Mean Green",
        5: "Villainous Violet",
        6: "Hot Rod",
    }

KILLSTREAKERS: Dict[int, str] = {
    int(k): str(v)
    for k, v in (_ig.get("killstreakers") or {}).items()
    if isinstance(v, str)
}

SPELL_FLAGS: Dict[int, str] = {
    int(k): str(v)
    for k, v in (_ig.get("spell_flags") or {}).items()
    if isinstance(v, str)
}
if not SPELL_FLAGS:
    SPELL_FLAGS = {
        1: "Fire Footprints",
        2: "Voices From Below",
        4: "Pumpkin Bombs",
        8: "Exorcism",
        16: "Paint Spell",
    }

STRANGE_PARTS: Dict[int, str] = {
    int(k): str(v)
    for k, v in (_ig.get("strange_parts") or {}).items()
    if isinstance(v, str)
}
if not STRANGE_PARTS:
    STRANGE_PARTS = {
        380: "Heavies Killed",
        381: "Buildings Destroyed",
        382: "Domination Kills",
        383: "Kills While Ubercharged",
        384: "Kills While Explosive Jumping",
        385: "Kills During Victory Time",
    }

EFFECTS: Dict[int, str] = {
    int(k): str(v)
    for k, v in (_schema.get("effects") or {}).items()
    if isinstance(v, str)
}

# Legacy aliases ------------------------------------------------------------
PAINT_MAP: Dict[int, Tuple[str, str]] = {
    k: (v["name"], v["hex"]) for k, v in PAINTS.items()
}
SHEEN_NAMES: Dict[int, str] = SHEENS
KILLSTREAK_TIERS = {
    1: "Killstreak",
    2: "Specialized Killstreak",
    3: "Professional Killstreak",
}
SPELL_BITFLAGS: Dict[int, Tuple[str, str]] = {
    1: ("Fire Footprints", "footprints"),
    2: ("Voices From Below", "voices"),
    4: ("Pumpkin Bombs", "pumpkin"),
    8: ("Exorcism", "exorcism"),
    16: ("Paint Spell", "paint_spell"),
}

__all__ = [
    "QUALITY_MAP",
    "ORIGIN_MAP",
    "PAINTS",
    "SHEENS",
    "KILLSTREAKERS",
    "SPELL_FLAGS",
    "STRANGE_PARTS",
    "EFFECTS",
    "TF2_SCHEMA",
    "ITEMS_GAME_CLEANED",
    "EFFECT_NAMES",
]
