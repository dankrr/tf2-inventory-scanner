import re
from typing import List

STEAMID2_RE = re.compile(r"STEAM_0:[01]:\d+")
STEAMID3_RE = re.compile(r"\[U:1:\d+\]")
STEAMID64_RE = re.compile(r"\b\d{17}\b")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Extract valid SteamID tokens from free-form text.

    The function splits the input on whitespace and returns unique IDs in
    the order encountered. Only strings matching SteamID2, SteamID3 or
    SteamID64 formats are kept.
    """

    tokens = re.split(r"\s+", raw_text.strip())
    ids: List[str] = []
    seen: set[str] = set()

    for token in tokens:
        if not token:
            continue
        if (
            STEAMID2_RE.fullmatch(token)
            or STEAMID3_RE.fullmatch(token)
            or STEAMID64_RE.fullmatch(token)
        ):
            if token not in seen:
                seen.add(token)
                ids.append(token)
    return ids
