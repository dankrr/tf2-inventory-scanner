from __future__ import annotations

from typing import Any, Dict

from . import local_data


def format_price(value_raw: float, currencies: Dict[str, Any]) -> str:
    """Return a refined metal value formatted in keys and refined metal."""

    try:
        value = float(value_raw)
    except (TypeError, ValueError):
        return ""

    key_price = 0.0
    try:
        key_price = float(currencies["keys"]["price"]["value_raw"])
    except Exception:  # pragma: no cover - defensive
        pass

    keys = int(value // key_price) if key_price > 0 else 0
    refined = value - keys * key_price if key_price > 0 else value

    parts: list[str] = []
    if keys:
        parts.append(f"{keys} Key" + ("s" if keys != 1 else ""))
    if refined > 0 or not parts:
        parts.append(f"{refined:.2f} ref")

    return " ".join(parts)


