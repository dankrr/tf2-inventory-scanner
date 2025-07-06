from __future__ import annotations

from typing import Any, Dict


def convert_price_to_keys_ref(
    value_raw: float, currency: str, currencies: Dict[str, Any]
) -> str:
    """Return human-readable price in keys and refined metal."""
    try:
        value = float(value_raw)
    except (TypeError, ValueError):
        return ""

    metal_info = currencies.get("metal") or {}
    key_info = currencies.get("keys") or {}
    cur_info = currencies.get(currency, {})

    metal_rate = float(metal_info.get("value_raw", 1.0))
    key_rate = float(key_info.get("value_raw", 0.0))
    cur_rate = float(cur_info.get("value_raw", 1.0))

    # Normalize to refined metal
    value_in_ref = value * cur_rate / metal_rate

    keys = 0
    if key_rate:
        keys = int(value_in_ref // key_rate)
    refined = value_in_ref - keys * key_rate

    parts = []
    if keys:
        parts.append(f"{keys} key" + ("s" if keys != 1 else ""))
    if refined > 0.01 or not parts:
        ref_str = f"{refined:.2f}".rstrip("0").rstrip(".")
        parts.append(f"{ref_str} ref")

    return " ".join(parts)


def convert_to_key_ref(value_refined: float) -> str:
    """Convert a refined metal value into a keys+refined string.

    Parameters
    ----------
    value_refined:
        The amount of refined metal to convert.

    Returns
    -------
    str
        A string in the form ``"<N> Keys <M.MM> Refined"``. Keys are computed
        using integer division and the remainder is formatted with two decimal
        places.
    """

    try:
        value = float(value_refined)
    except (TypeError, ValueError):
        return ""

    key_price = 50.0

    keys = int(value // key_price)
    refined = value - keys * key_price

    parts = []
    if keys:
        parts.append(f"{keys} Key" + ("s" if keys != 1 else ""))
    if refined > 0.0 or not parts:
        parts.append(f"{refined:.2f} Refined")

    return " ".join(parts)
