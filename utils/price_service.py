from __future__ import annotations

from typing import Any, Dict

from . import local_data


def convert_price_to_keys_ref(
    value_raw: float, currency: str, currencies: Dict[str, Any]
) -> str:
    """Return human-readable price in keys and refined metal."""

    try:
        if currency == "keys":
            return f"{round(value_raw, 2)} Keys"

        ref_per_key = currencies["keys"]["price"]["value_raw"]
        if not ref_per_key or ref_per_key <= 0:
            return f"{round(value_raw, 2)} Refined"

        total_ref = value_raw
        keys = int(total_ref // ref_per_key)
        refined = round(total_ref - keys * ref_per_key, 2)

        if keys > 0 and refined > 0:
            return f"{keys} Keys {refined} Refined"
        elif keys > 0:
            return f"{keys} Keys"
        else:
            return f"{refined} Refined"
    except Exception:
        return f"{round(value_raw, 2)} {currency}"


def convert_to_key_ref(
    value_refined: float, currencies: Dict[str, Any] | None = None
) -> str:
    """Convert a refined metal value into a keys+refined string.

    Parameters
    ----------
    value_refined:
        The amount of refined metal to convert.
    currencies:
        Mapping of currency data loaded from ``local_data``. If ``None``,
        ``local_data.CURRENCIES`` will be used.

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

    if currencies is None:
        currencies = local_data.CURRENCIES

    key_price = 50.0
    try:
        key_price = float(currencies["keys"]["price"]["value_raw"])
    except Exception:
        pass

    keys = int(value // key_price)
    refined = value - keys * key_price

    parts = []
    if keys:
        parts.append(f"{keys} Key" + ("s" if keys != 1 else ""))
    if refined > 0.0 or not parts:
        parts.append(f"{refined:.2f} Refined")

    return " ".join(parts)
