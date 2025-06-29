import os
import re
import asyncio
import time
import sys
from typing import List, Dict, Any
from types import SimpleNamespace

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash
from utils.id_parser import extract_steam_ids
from utils.schema_fetcher import ensure_schema_cached
from utils.inventory_processor import enrich_inventory
from utils import steam_api_client as sac
from utils import items_game_cache
from utils import local_data
from utils.autobot_schema_cache import ensure_all_cached

load_dotenv()
if not os.getenv("STEAM_API_KEY"):
    raise RuntimeError(
        "Required env var missing: STEAM_API_KEY. Make sure you have a .env file or export it."
    )

if "--refresh" in sys.argv[1:]:
    from utils import autobot_schema_cache
    from utils import local_data

    print(
        "\N{anticlockwise open circle arrow} Refresh requested: refetching TF2 schema and items_game..."
    )
    autobot_schema_cache.ensure_all_cached(refresh=True)
    local_data.load_files()
    print("\N{CHECK MARK} Autobot schema refreshed")
    print(
        "\N{CHECK MARK} Refresh complete. Restart app normally without --refresh to start server."
    )
    raise SystemExit(0)

STEAM_API_KEY = os.environ["STEAM_API_KEY"]

app = Flask(__name__)

ITEMS_GAME_READY_FUTURE = items_game_cache.ensure_future()
MAX_MERGE_MS = 0

ensure_all_cached()
SCHEMA = ensure_schema_cached()
print(f"Loaded {len(SCHEMA)} schema items")
local_data.load_files()

# --- Utility functions ------------------------------------------------------


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
    return {"items": items, "status": status}


async def build_user_data_async(steamid64: str) -> Dict[str, Any]:
    """Asynchronously build user card data."""
    inv_task = asyncio.to_thread(fetch_inventory, steamid64)
    await items_game_cache.wait_until_ready()
    t1 = time.perf_counter()
    summary = await asyncio.to_thread(get_player_summary, steamid64)
    inv_result = await inv_task
    t2 = time.perf_counter()

    items = inv_result.get("items", [])
    if not isinstance(items, list):
        items = []
    status = inv_result.get("status", "failed")

    summary.update({"steamid": steamid64, "items": items, "status": status})

    inventory_fetch_ms = int((t2 - t1) * 1000)
    merge_ms = int((time.perf_counter() - t2) * 1000)
    global MAX_MERGE_MS
    MAX_MERGE_MS = max(MAX_MERGE_MS, merge_ms)
    print(
        f"inventory_fetch_ms={inventory_fetch_ms} merge_ms={merge_ms}",
        flush=True,
    )

    return summary


def build_user_data(steamid64: str) -> Dict[str, Any]:
    """Return a dictionary for rendering a single user card."""

    return asyncio.run(build_user_data_async(steamid64))


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
                ids=[],
            )
    return render_template(
        "index.html",
        users=users,
        steamids=steamids_input,
        ids=ids,
        debug_ms=MAX_MERGE_MS if os.getenv("FLASK_DEBUG") else None,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
