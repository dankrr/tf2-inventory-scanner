import re
from typing import List

STEAMID2_RE = re.compile(r"STEAM_0:[01]:\d+")
STEAMID3_RE = re.compile(r"\[U:1:\d+\]")
STEAMID64_RE = re.compile(r"\b\d{17}\b")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Return valid SteamID tokens found in ``raw_text``.

    The function scans the input for SteamID64, SteamID2 and SteamID3 patterns
    and returns them in the order encountered, skipping any other text. Duplicate
    IDs are removed while preserving first occurrence order.
    """

    pattern = re.compile(
        r"(STEAM_0:[01]:\d+|\[U:1:\d+\]|\b7656119\d{10}\b)", re.IGNORECASE
    )
    ids: List[str] = []
    seen: set[str] = set()

    for match in pattern.finditer(raw_text):
        token = match.group(0)
        if token not in seen:
            seen.add(token)
            ids.append(token)

    return ids
