from __future__ import annotations

from typing import Any, Dict

from . import local_data


def convert_price_to_keys_ref(
    value_raw: float, currency: str, currencies: Dict[str, Any]
) -> str:
    """Return human-readable price in keys and refined metal.

    ``value_raw`` from the Backpack.tf price dump is always expressed in
    refined metal, even when the ``currency`` field is ``"keys"``. This
    helper converts that metal value into a formatted string using the
    current key price from ``currencies``.
    """

    try:
        value = float(value_raw)
    except (TypeError, ValueError):
        return ""

    curr_lower = str(currency or "").lower()

    key_price = 0.0
    try:
        key_price = float(currencies["keys"]["price"]["value_raw"])
    except Exception:
        pass

    # Determine if ``value_raw`` is actually in refined metal units.
    in_ref = curr_lower in {"metal", "ref", "refined"} or (
        curr_lower == "keys" and key_price > 0 and value >= key_price
    )

    if in_ref:
        if key_price > 0:
            keys = int(value // key_price)
            refined = round(value - keys * key_price, 2)
            if keys and refined:
                return f"{keys} Keys {refined} Refined"
            if keys:
                return f"{keys} Keys"
            return f"{refined} Refined"
        return f"{round(value, 2)} Refined"

    if curr_lower == "keys":
        if value.is_integer():
            return f"{int(value)} Keys"
        return f"{round(value, 2)} Keys"

    return f"{round(value, 2)} {currency}"


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
