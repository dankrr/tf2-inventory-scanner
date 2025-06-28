import os
import re
from typing import List, Dict, Any
from types import SimpleNamespace

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash
from utils.id_parser import extract_steam_ids
from utils.schema_fetcher import ensure_schema_cached
from utils.inventory_processor import enrich_inventory
from utils import steam_api_client as sac
from services import pricing_service

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
BACKPACK_API_KEY = os.getenv("BACKPACK_API_KEY")

if not STEAM_API_KEY or not BACKPACK_API_KEY:
    raise ValueError("STEAM_API_KEY and BACKPACK_API_KEY must be set")

app = Flask(__name__)

SCHEMA = ensure_schema_cached()
print(f"Loaded {len(SCHEMA)} schema items")

PRICE_CACHE: Dict[str, Any] = {}
KEY_REF_RATE: float = 0.0

# --- Utility functions ------------------------------------------------------


def build_sku(item: Dict[str, Any]) -> str:
    """Return backpack.tf SKU for an item."""
    parts = [str(item.get("defindex")), str(item.get("quality_id", 0))]
    if item.get("australium"):
        parts.append("australium")
    if item.get("uncraftable"):
        parts.append("uncraftable")
    if item.get("effect"):
        parts.append(f"u{item['effect']}")
    return ";".join(parts)


def fetch_prices() -> None:
    """Load price cache and currency rates once per run."""
    global PRICE_CACHE, KEY_REF_RATE
    if PRICE_CACHE and KEY_REF_RATE:
        return
    PRICE_CACHE = pricing_service.ensure_price_cache()
    KEY_REF_RATE = pricing_service.ensure_currency_rates()


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
            sku = build_sku(item)
            entry = PRICE_CACHE.get(sku)
            if entry and entry.get("value") is not None:
                item["price"] = "Price: " + pricing_service.format_price(
                    float(entry["value"]), KEY_REF_RATE
                )
                item["unknown"] = False
            else:
                item["price"] = "Price: Unknown"
                item["unknown"] = True
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
    fetch_prices()
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
    ids: List[str] = []
    invalid: List[str] = []
    if request.method == "POST":
        steamids_input = request.form.get("steamids", "")
        tokens = re.split(r"\s+", steamids_input.strip())
        raw_ids = extract_steam_ids(steamids_input)
        invalid = [t for t in tokens if t and t not in raw_ids]
        ids = [sac.convert_to_steam64(t) for t in raw_ids]
        print(f"Parsed {len(ids)} valid IDs, {len(invalid)} tokens ignored")
        if not ids:
            flash("No valid Steam IDs found!")
            return render_template(
                "index.html",
                users=users,
                steamids=steamids_input,
                valid_count=0,
                invalid_count=len(invalid),
            )
        fetch_prices()
    return render_template(
        "index.html",
        users=users,
        steamids=steamids_input,
        valid_count=len(ids) if request.method == "POST" else 0,
        invalid_count=len(invalid) if request.method == "POST" else 0,
        ids=ids,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
