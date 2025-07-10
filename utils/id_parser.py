import re
from typing import List

STEAMID2_RE = re.compile(r"STEAM_0:[01]:\d+")
STEAMID3_RE = re.compile(r"\[U:1:\d+\]")
STEAMID64_RE = re.compile(r"\b\d{17}\b")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Extract potential SteamID tokens from free-form text.

    The function splits the input on whitespace and returns unique tokens in the
    order encountered. Tokens matching ``STEAMID2``, ``STEAMID3`` or
    ``STEAMID64`` patterns are kept, but any other non-empty strings are also
    returned so they may be resolved as vanity URLs later.
    """

    tokens = re.split(r"\s+", raw_text.strip())
    ids: List[str] = []
    seen: set[str] = set()

    for token in tokens:
        token = token.strip('"')
        if not token:
            continue
        if token not in seen:
            seen.add(token)
            ids.append(token)
    return ids
