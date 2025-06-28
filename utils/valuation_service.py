def format_price(price_obj, key_price_ref):
    cur, val = price_obj["currency"], price_obj["value"]
    if cur == "metal":
        keys = int(val // key_price_ref)
        ref = round(val - keys * key_price_ref, 2)
    elif cur == "keys":
        keys = int(val)
        ref = round((val - keys) * key_price_ref, 2)
    else:
        return ""
    return (
        f"{keys} key{'s' if keys != 1 else ''} {ref:.2f} ref"
        if keys or ref
        else "0 ref"
    )
