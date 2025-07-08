import difflib
from typing import Iterable, Optional


def best_match_from_keys(query: str, keys: Iterable[str]) -> Optional[str]:
    """Return the closest match to ``query`` from ``keys`` using :func:`difflib.get_close_matches`.

    Parameters
    ----------
    query:
        The search string to compare.
    keys:
        Collection of possible target strings.

    Returns
    -------
    Optional[str]
        The closest matching key or ``None`` if no match exceeds the cutoff.
    """
    matches = difflib.get_close_matches(query, list(keys), n=1, cutoff=0.6)
    return matches[0] if matches else None
