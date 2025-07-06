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
        parts.append(f"{refined:.2f} Refined")

    return " ".join(parts)


def convert_price_to_keys_ref(
    value_raw: float, currency: str, currencies: Dict[str, Any]
) -> str:
    """Backward compatible wrapper calling :func:`format_price`."""

    return format_price(value_raw, currencies)


def convert_to_key_ref(
    value_refined: float, currencies: Dict[str, Any] | None = None
) -> str:
    """Backward compatible wrapper for :func:`format_price`."""

    if currencies is None:
        currencies = local_data.CURRENCIES

    return format_price(value_refined, currencies)
