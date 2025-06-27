import os
import re
from typing import List, Dict, Any, Tuple
from types import SimpleNamespace

from dotenv import load_dotenv

import requests
from flask import Flask, render_template, request
from utils.schema_fetcher import ensure_schema_cached
from utils.inventory_processor import enrich_inventory
from utils import steam_api_client as sac

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
BACKPACK_API_KEY = os.getenv("BACKPACK_API_KEY")

if not STEAM_API_KEY or not BACKPACK_API_KEY:
    raise ValueError("STEAM_API_KEY and BACKPACK_API_KEY must be set")

app = Flask(__name__)

SCHEMA = ensure_schema_cached()
print(f"Loaded {len(SCHEMA)} schema items")

BACKPACK_PRICES: Dict[str, float] = {}

# --- Utility functions ------------------------------------------------------


def parse_steamids(raw: str) -> Tuple[List[str], List[str]]:
    """Return valid SteamID64 strings and a list of invalid tokens.

    The input is split on any non-alphanumeric characters to support a mix of
    newline, comma or space separated values.  Each token is normalised using
    :func:`steamid_to_64`.  Invalid values are skipped and returned in a second
    list.  Duplicate IDs are removed while preserving order.
    """

    tokens = re.split(r"[^0-9A-Za-z:\[\]_]+", raw)
    valid: List[str] = []
    invalid: List[str] = []
    seen: set[str] = set()

    for token in tokens:
        token = token.strip()
        if not token:
            continue
        try:
            sid64 = steamid_to_64(token)
        except Exception:
            invalid.append(token)
            continue
        if sid64 not in seen:
            seen.add(sid64)
            valid.append(sid64)

    return valid, invalid


def steamid_to_64(id_str: str) -> str:
    """Convert various SteamID forms to SteamID64."""
    # SteamID64
    if re.fullmatch(r"\d{17}", id_str):
        return id_str

    # SteamID2: STEAM_X:Y:Z
    if id_str.startswith("STEAM_"):
        try:
            _, y, z = id_str.split(":")
            y = int(y.split("_")[1]) if "_" in y else int(y)
            z = int(z)
        except (ValueError, IndexError):
            raise ValueError(f"Invalid SteamID2: {id_str}") from None
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    # SteamID3: [U:1:Z]
    if id_str.startswith("[U:"):
        match = re.match(r"\[U:(\d+):(\d+)\]", id_str)
        if match:
            z = int(match.group(2))
            return str(z + 76561197960265728)
        match = re.match(r"\[U:1:(\d+)\]", id_str)
        if match:
            z = int(match.group(1))
            return str(z + 76561197960265728)

    # Vanity URL
    url = (
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
        f"?key={STEAM_API_KEY}&vanityurl={id_str}"
    )
    print(f"Resolving vanity URL {id_str}")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError(f"Unable to resolve vanity URL: {id_str}")
    return data["steamid"]


def fetch_prices() -> None:
    """Fetch price data from backpack.tf and populate BACKPACK_PRICES."""
    global BACKPACK_PRICES
    if BACKPACK_PRICES:
        return
    url = f"https://backpack.tf/api/IGetPrices/v4?key={BACKPACK_API_KEY}"
    print("Fetching price data from backpack.tf")
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("response", {})
    if data.get("success") != 1:
        raise ValueError("Invalid response from backpack.tf")
    items = data.get("items", {})
    for name, info in items.items():
        price = extract_price(info)
        if price is not None:
            BACKPACK_PRICES[name] = price


def extract_price(item_data: Dict[str, Any]) -> float | None:
    """Extract a metal price from backpack.tf price data."""
    prices = item_data.get("prices", {})
    for quality in prices.values():
        if not isinstance(quality, dict):
            continue
        for tradable in quality.values():
            node = None
            if isinstance(tradable, list) and tradable:
                node = tradable[0]
            elif isinstance(tradable, dict):
                node = tradable
            if node and node.get("currency") == "metal":
                return float(node.get("value"))
    return None


def get_player_summary(steamid64: str) -> Dict[str, Any]:
    """Return profile name, avatar URL and TF2 playtime for a user."""
    print(f"Fetching player summary for {steamid64}")
    players = sac.get_player_summaries([steamid64])
    profile = f"https://steamcommunity.com/profiles/{steamid64}"
    if players:
        player = players[0]
        username = player.get("personaname", steamid64)
        avatar = player.get("avatarfull", "")
        profile = player.get("profileurl", profile)
    else:
        username = steamid64
        avatar = ""

    playtime = sac.get_tf2_playtime_hours(steamid64)

    return {
        "username": username,
        "avatar": avatar,
        "playtime": round(playtime, 1),
        "profile": profile,
    }


def fetch_inventory(steamid64: str) -> Dict[str, Any]:
    """Fetch TF2 inventory items for a user and return items with a status."""
    status, data = sac.fetch_inventory(steamid64)
    items: List[Dict[str, Any]] = []
    if status == "parsed":
        items = enrich_inventory(data)
        for item in items:
            price = BACKPACK_PRICES.get(item["item_name"])
            item["price"] = f"{price:.2f}" if price is not None else "?"
    return {"items": items, "status": status}


def build_user_data(steamid64: str) -> Dict[str, Any]:
    """Return a dictionary for rendering a single user card."""

    try:
        summary = get_player_summary(steamid64)
    except Exception as exc:
        print(f"Error fetching summary for {steamid64}: {exc}")
        summary = {
            "username": steamid64,
            "avatar": "",
            "playtime": 0.0,
            "profile": f"https://steamcommunity.com/profiles/{steamid64}",
        }

    try:
        inv_result = fetch_inventory(steamid64)
    except Exception as exc:
        print(f"Error processing {steamid64}: {exc}")
        inv_result = {"items": [], "status": "failed"}

    items = inv_result.get("items", [])
    if not isinstance(items, list):
        items = []
    status = inv_result.get("status", "failed")

    summary.update({"steamid": steamid64, "items": items, "status": status})
    return summary


def normalize_user_payload(user: Dict[str, Any]) -> SimpleNamespace:
    """Return a namespace with ``items`` guaranteed to be a list."""

    items = user.get("items", [])
    user["items"] = items if isinstance(items, list) else []
    return SimpleNamespace(**user)


def fetch_and_process_single_user(steamid64: int) -> str:
    user = build_user_data(str(steamid64))
    user = normalize_user_payload(user)
    return render_template("_user.html", user=user)


@app.post("/retry/<int:steamid64>")
def retry_single(steamid64: int):
    """Reprocess a single user and return a rendered snippet."""
    return fetch_and_process_single_user(steamid64)


# --- Flask routes -----------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
def index():
    users: List[Dict[str, Any]] = []
    steamids_input = ""
    if request.method == "POST":
        steamids_input = request.form.get("steamids", "")
        ids, invalid = parse_steamids(steamids_input)
        print(f"Parsed {len(ids)} valid IDs, {len(invalid)} invalid tokens")
        fetch_prices()
        for sid64 in ids:
            user = build_user_data(sid64)
            items = user.get("items")
            status = user.get("status")
            if status == "failed":
                status = "incomplete"
            elif status not in ("parsed", "incomplete"):
                status = "private"
            if status != "parsed":
                items = []
            user["status"] = status
            user["items"] = items
            user = normalize_user_payload(user)
            users.append(user)
    return render_template(
        "index.html",
        users=users,
        steamids=steamids_input,
        valid_count=len(ids) if request.method == "POST" else 0,
        invalid_count=len(invalid) if request.method == "POST" else 0,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
