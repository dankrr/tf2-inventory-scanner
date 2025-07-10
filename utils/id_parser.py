import re
from typing import List

STEAMID2_RE = re.compile(r"^STEAM_0:[01]:\d+$")
STEAMID3_RE = re.compile(r"^\[U:1:\d+\]$")
STEAMID64_RE = re.compile(r"^\d{17}$")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Return unique SteamIDs from the given text.

    Each non-empty line is checked against the supported formats. Lines
    containing anything other than a valid SteamID64, SteamID2 or
    SteamID3 token are ignored.
    """

    lines = raw_text.splitlines()
    ids: List[str] = []
    seen: set[str] = set()

    for line in lines:
        token = line.strip()
        if not token:
            continue
        if (
            STEAMID64_RE.fullmatch(token)
            or STEAMID2_RE.fullmatch(token)
            or STEAMID3_RE.fullmatch(token)
        ):
            if token not in seen:
                seen.add(token)
                ids.append(token)
    return ids
