import os
import re
import sys
import logging
from typing import List, Dict, Any
from types import SimpleNamespace

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash
from utils.id_parser import extract_steam_ids
from utils.schema_fetcher import ensure_schema_cached
from utils.inventory_processor import enrich_inventory
from utils import steam_api_client as sac
from utils import price_fetcher

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
BACKPACK_API_KEY = os.getenv("BACKPACK_API_KEY")

if not STEAM_API_KEY or not BACKPACK_API_KEY:
    raise ValueError("STEAM_API_KEY and BACKPACK_API_KEY must be set")

app = Flask(__name__)

SCHEMA = ensure_schema_cached()
logger.info("Loaded %s schema items", len(SCHEMA))

PRICE_CACHE: Dict[str, Any] = {}
KEY_REF_RATE: float = 0.0

# --- Utility functions ------------------------------------------------------


def fetch_prices() -> None:
    """Load price cache and currency rates once per run."""
    global PRICE_CACHE, KEY_REF_RATE
    if PRICE_CACHE and KEY_REF_RATE:
        return
    data = price_fetcher.ensure_prices_cached()
    PRICE_CACHE = data.get("items", {}) if isinstance(data, dict) else {}
    currencies = price_fetcher.ensure_currencies_cached()
    metal_val = currencies.get("metal", {}).get("value")
    key_val = currencies.get("keys", {}).get("value")
    KEY_REF_RATE = key_val / metal_val if metal_val else 0.0


def get_player_summary(steamid64: str) -> Dict[str, Any]:
    """Return profile name, avatar URL and TF2 playtime for a user."""
    logger.debug("Fetching player summary for %s", steamid64)
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
        items = enrich_inventory(data, PRICE_CACHE, KEY_REF_RATE)
    return {"items": items, "status": status}


def build_user_data(steamid64: str) -> Dict[str, Any]:
    """Return a dictionary for rendering a single user card."""

    try:
        summary = get_player_summary(steamid64)
    except Exception as exc:
        logger.error("Error fetching summary for %s: %s", steamid64, exc)
        summary = {
            "username": steamid64,
            "avatar": "",
            "playtime": 0.0,
            "profile": f"https://steamcommunity.com/profiles/{steamid64}",
        }

    try:
        inv_result = fetch_inventory(steamid64)
    except Exception as exc:
        logger.error("Error processing %s: %s", steamid64, exc)
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
    logger.info("Retry start for %s", steamid64)
    try:
        fetch_prices()
        if not SCHEMA:
            logger.warning("Schema cache missing or invalid")
        if not PRICE_CACHE or not KEY_REF_RATE:
            logger.warning("Price cache missing or invalid")

        status, raw_data = sac.fetch_inventory(str(steamid64))
        assets = raw_data.get("items") if isinstance(raw_data, dict) else None
        if not assets:
            logger.warning("Inventory fetch for %s returned no assets", steamid64)
        else:
            logger.debug("Fetched %s raw items for %s", len(assets), steamid64)

        if status != "parsed":
            logger.info("Inventory fetch status for %s: %s", steamid64, status)

        parsed_items = (
            enrich_inventory(raw_data, PRICE_CACHE, KEY_REF_RATE) if assets else []
        )
        if parsed_items:
            logger.info("Parsed %s items for %s", len(parsed_items), steamid64)
        else:
            logger.warning("No parsed items generated for %s", steamid64)

        user = get_player_summary(str(steamid64))
        user.update({"steamid": steamid64, "items": parsed_items, "status": status})
        logger.info("User data updated for %s", steamid64)
        user_ns = normalize_user_payload(user)
        return render_template("_user.html", user=user_ns)
    except Exception:
        logger.exception("Retry %s: unexpected error", steamid64)
        raise


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
        logger.info("Parsed %s valid IDs, %s tokens ignored", len(ids), len(invalid))
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
