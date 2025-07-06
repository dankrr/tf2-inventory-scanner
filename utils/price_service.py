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
        parts.append(f"{keys} Key" + ("s" if keys != 1 else ""))
    if refined > 0.01 or not parts:
        ref_str = f"{refined:.2f}".rstrip("0").rstrip(".")
        parts.append(f"{ref_str} Refined")

    return " ".join(parts)
