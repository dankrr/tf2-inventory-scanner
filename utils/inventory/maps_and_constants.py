# Static maps and IDs used across inventory processing.

QUALITY_MAP = {
    0: ("Normal", "#7f7f7f"),
    1: ("Genuine", "#4D7455"),
    3: ("Vintage", "#476291"),
    5: ("Unusual", "#8650AC"),
    6: ("Unique", "#FFD700"),
    11: ("Strange", "#CF6A32"),
    13: ("Haunted", "#0c8657"),
    14: ("Collector's", "#AA0000"),
    15: ("Decorated Weapon", "#FAFAFA"),
}

STRANGE_QUALITY_ID = 11

DEFAULT_QUALITIES = {"Strange", "Unique", "Normal"}

WAR_PAINT_TOOL_DEFINDEXES = {5681, 5682, 5683}

KILLSTREAK_KIT_DEFINDEXES = {6527, 6523, 6526}
KILLSTREAK_FABRICATOR_DEFINDEXES = {20002, 20003}

FABRICATOR_PART_IDS = {5701, 5702, 5703, 5704, 5705, 5706, 5707}

__all__ = [
    "QUALITY_MAP",
    "STRANGE_QUALITY_ID",
    "DEFAULT_QUALITIES",
    "WAR_PAINT_TOOL_DEFINDEXES",
    "KILLSTREAK_KIT_DEFINDEXES",
    "KILLSTREAK_FABRICATOR_DEFINDEXES",
    "FABRICATOR_PART_IDS",
]
