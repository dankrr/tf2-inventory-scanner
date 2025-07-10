import re
from typing import List

STEAMID2_RE = re.compile(r"STEAM_0:[01]:\d+")
STEAMID3_RE = re.compile(r"\[U:1:\d+\]")
STEAMID64_RE = re.compile(r"\b\d{17}\b")


def convert_to_steam64(token: str) -> str:
    """Convert a SteamID token to ``SteamID64``.

    Parameters
    ----------
    token:
        SteamID in ``SteamID64``, ``SteamID2`` or ``SteamID3`` format.

    Returns
    -------
    str
        The normalized ``SteamID64`` value.

    Raises
    ------
    ValueError
        If ``token`` is malformed or unsupported.
    """

    if STEAMID64_RE.fullmatch(token):
        return token

    if token.startswith("STEAM_"):
        try:
            _, y, z = token.split(":")
            y = int(y.split("_")[1]) if "_" in y else int(y)
            z = int(z)
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid SteamID2: {token}") from exc
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    if token.upper().startswith("[U:"):
        match = re.match(r"\[U:(\d+):(\d+)\]", token, re.IGNORECASE)
        if match:
            z = int(match.group(2))
            return str(z + 76561197960265728)
        match = re.match(r"\[U:1:(\d+)\]", token, re.IGNORECASE)
        if match:
            z = int(match.group(1))
            return str(z + 76561197960265728)
        raise ValueError(f"Invalid SteamID3: {token}")

    raise ValueError(f"Unrecognized SteamID token: {token}")


def extract_steam_ids(raw_text: str) -> List[str]:
    """Return unique ``SteamID64`` values parsed from ``raw_text``.

    The function scans ``raw_text`` for ``SteamID64``, ``SteamID2`` and
    ``SteamID3`` tokens and converts each match to ``SteamID64``. Duplicate IDs
    are removed while preserving the first occurrence order.
    """

    pattern = re.compile(
        r"(STEAM_0:[01]:\d+|\[U:1:\d+\]|\b7656119\d{10}\b)", re.IGNORECASE
    )
    ids: List[str] = []
    seen: set[str] = set()

    for match in pattern.finditer(raw_text):
        token = match.group(0)
        try:
            sid = convert_to_steam64(token)
        except ValueError:
            continue
        if sid not in seen:
            seen.add(sid)
            ids.append(sid)

    return ids
