import os
import re
import asyncio
import time
import queue
import concurrent.futures
import threading
from pathlib import Path
import json
import argparse
import psutil
from typing import List, Dict, Any
from types import SimpleNamespace

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, jsonify
from utils.id_parser import extract_steam_ids
from utils.inventory_processor import enrich_inventory
import utils.inventory_processor as ip

from utils import steam_api_client as sac
from utils import local_data
from utils import constants as consts
from utils.price_loader import (
    ensure_prices_cached,
    ensure_currencies_cached,
)

load_dotenv()
if not os.getenv("STEAM_API_KEY"):
    raise RuntimeError(
        "Required env var missing: STEAM_API_KEY. Make sure you have a .env file or export it."
    )

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--refresh", action="store_true")
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--test", action="store_true")
ARGS, _ = parser.parse_known_args()

if ARGS.refresh:
    from utils.schema_provider import SchemaProvider

    print(
        "\N{ANTICLOCKWISE OPEN CIRCLE ARROW} Refresh requested: refetching TF2 schema..."
    )
    provider = SchemaProvider(cache_dir="cache/schema")
    provider.refresh_all(verbose=True)
    price_path = ensure_prices_cached(refresh=True)
    curr_path = ensure_currencies_cached(refresh=True)
    print(f"\N{CHECK MARK} Saved {price_path}")
    print(f"\N{CHECK MARK} Saved {curr_path}")
    print(
        "\N{CHECK MARK} Refresh complete. Restart app normally without --refresh to start server."
    )
    raise SystemExit(0)

TEST_MODE = ARGS.test
TEST_STEAMID: str = ""
TEST_INVENTORY_RAW: Dict[str, Any] | None = None
TEST_INVENTORY_STATUS: str = ""

STEAM_API_KEY = os.environ["STEAM_API_KEY"]

app = Flask(__name__)

fetch_queue: queue.Queue[tuple[str, int]] = queue.Queue()

MAX_MERGE_MS = 0
local_data.load_files(auto_refetch=True, verbose=ARGS.verbose)
_prices_path = ensure_prices_cached(refresh=ARGS.refresh)
_currencies_path = ensure_currencies_cached(refresh=ARGS.refresh)
try:
    with open(_currencies_path) as f:
        local_data.CURRENCIES = json.load(f)["response"]["currencies"]
except Exception:
    local_data.CURRENCIES = {}

# --- Utility functions ------------------------------------------------------

IGNORED_STACK_KEYS = {"level", "custom_description", "custom_name", "origin"}


def kill_process_on_port(port: int) -> None:
    """Terminate any process currently listening on ``port``."""

    for conn in psutil.net_connections(kind="tcp"):
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            pid = conn.pid
            if pid and pid != os.getpid():
                try:
                    psutil.Process(pid).terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass


def stack_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a list of items with identical attributes collapsed.

    Items are grouped by all fields except those in ``IGNORED_STACK_KEYS``.
    Each returned dictionary includes a ``quantity`` key indicating how many
    instances were merged.
    """

    grouped: Dict[str, Dict[str, Any]] = {}
    for itm in items:
        if not isinstance(itm, dict):
            continue
        key_obj = {k: v for k, v in itm.items() if k not in IGNORED_STACK_KEYS}
        try:
            key = json.dumps(key_obj, sort_keys=True)
        except TypeError:
            # Fallback: skip items with unserializable fields
            key = str(key_obj)
        if key in grouped:
            grouped[key]["quantity"] += 1
        else:
            new_item = itm.copy()
            new_item.setdefault("quantity", 1)
            grouped[key] = new_item
    return list(grouped.values())


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
    global TEST_INVENTORY_RAW, TEST_INVENTORY_STATUS

    if TEST_MODE and steamid64 == TEST_STEAMID and TEST_INVENTORY_RAW is not None:
        status = TEST_INVENTORY_STATUS or "parsed"
        data = TEST_INVENTORY_RAW
    else:
        status, data = sac.fetch_inventory(steamid64)
    items: List[Dict[str, Any]] = []
    if status == "parsed":
        try:
            items = enrich_inventory(data, valuation_service=ip.get_valuation_service())
        except Exception:
            app.logger.exception("Failed to enrich inventory for %s", steamid64)
            status = "failed"
            items = []
    return {"items": items, "status": status}


async def build_user_data_async(steamid64: str) -> Dict[str, Any]:
    """Asynchronously build user card data."""
    inv_task = asyncio.to_thread(fetch_inventory, steamid64)
    t1 = time.perf_counter()
    summary = await asyncio.to_thread(get_player_summary, steamid64)
    inv_result = await inv_task
    t2 = time.perf_counter()

    items = inv_result.get("items", [])
    if not isinstance(items, list):
        items = []
    else:
        items = stack_items(items)
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


def fetch_inventory_concurrently(
    steam_ids: List[str], max_workers: int = 4, max_retries: int = 1
) -> tuple[List[SimpleNamespace], List[str]]:
    """Fetch multiple inventories concurrently using worker threads."""

    for sid in steam_ids:
        fetch_queue.put((sid, 0))

    results: List[SimpleNamespace] = []
    failed: List[str] = []
    lock = threading.Lock()

    def worker() -> None:
        while True:
            try:
                steamid, tries = fetch_queue.get_nowait()
            except queue.Empty:
                break
            try:
                data = build_user_data(str(steamid))
                if data.get("status") == "parsed":
                    user = normalize_user_payload(data)
                    with lock:
                        results.append(user)
                else:
                    raise RuntimeError("inventory not parsed")
            except Exception:
                app.logger.exception("Failed to fetch %s", steamid)
                if tries < max_retries:
                    fetch_queue.put((steamid, tries + 1))
                else:
                    with lock:
                        failed.append(str(steamid))
            finally:
                fetch_queue.task_done()

    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(worker) for _ in range(max_workers)]
        for fut in concurrent.futures.as_completed(futures):
            app.logger.info("Worker finished: %s", fut)

    return results, failed


def fetch_and_process_single_user(steamid64: int) -> str:
    user = build_user_data(str(steamid64))
    user = normalize_user_payload(user)
    return render_template("_user.html", user=user)


def _setup_test_mode() -> None:
    """Initialize test mode and preload inventory data."""

    global TEST_STEAMID, TEST_INVENTORY_RAW, TEST_INVENTORY_STATUS

    cache_dir = Path("cached_inventories")
    cache_dir.mkdir(exist_ok=True)
    last_file = cache_dir / "last.txt"

    steamid: str | None = None
    if last_file.exists():
        last = last_file.read_text().strip()
        ans = input(f"Reuse last test inventory ({last})? (y/n): ").strip().lower()
        if ans.startswith("y"):
            steamid = last

    if not steamid:
        steamid = input("Enter SteamID64 for test inventory: ").strip()

    last_file.write_text(steamid)

    cache_file = cache_dir / f"{steamid}.json"

    while True:
        if cache_file.exists():
            ans = (
                input(
                    f"Cached inventory found for {steamid}. Use cached version? (y/n): "
                )
                .strip()
                .lower()
            )
            if ans.startswith("y"):
                with cache_file.open() as f:
                    TEST_INVENTORY_RAW = json.load(f)
                TEST_INVENTORY_STATUS = "parsed"
                print("Loaded cached inventory for testing.")
                break
        status, data = sac.fetch_inventory(steamid)
        if status != "failed":
            TEST_INVENTORY_RAW = data
            TEST_INVENTORY_STATUS = status
            with cache_file.open("w") as f:
                json.dump(data, f)
            break
        print(
            "Failed to fetch inventory. Steam may be down or unreachable. Try again later."
        )
        if input("Retry? (y/n): ").strip().lower() != "y":
            raise SystemExit(1)

    TEST_STEAMID = steamid
    user = normalize_user_payload(build_user_data(steamid))
    app.config["PRELOADED_USERS"] = [user]
    app.config["TEST_STEAMID"] = steamid


@app.post("/retry/<int:steamid64>")
def retry_single(steamid64: int):
    """Reprocess a single user and return a rendered snippet."""
    return fetch_and_process_single_user(steamid64)


@app.post("/fetch_batch")
def fetch_batch() -> Any:
    """Fetch multiple inventories concurrently and return rendered HTML."""

    data = request.get_json(silent=True) or {}
    ids = [str(i) for i in data.get("ids", []) if i]
    results, failed = fetch_inventory_concurrently(ids)
    html = [render_template("_user.html", user=u) for u in results]
    return jsonify({"html": html, "failed": failed})


@app.get("/api/constants")
def api_constants():
    """Return static constant mappings for client usage."""
    return jsonify(
        {
            "paint_colors": consts.PAINT_COLORS,
            "sheen_names": consts.SHEEN_NAMES,
            "killstreak_sheen_colors": consts.KILLSTREAK_SHEEN_COLORS,
            "killstreak_tiers": consts.KILLSTREAK_TIERS,
            "killstreak_effects": consts.KILLSTREAK_EFFECTS,
            "origin_map": consts.ORIGIN_MAP,
        }
    )


# --- Flask routes -----------------------------------------------------------


@app.route("/", methods=["GET", "POST"])
def index():
    users: List[Dict[str, Any]] = []
    steamids_input = ""
    ids: List[str] = []
    invalid: List[str] = []
    if request.method == "GET" and app.config.get("PRELOADED_USERS"):
        users = app.config.get("PRELOADED_USERS", [])
        steamids_input = app.config.get("TEST_STEAMID", "")
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
    port = int(os.getenv("PORT", 5000))
    kill_process_on_port(port)
    if TEST_MODE:
        _setup_test_mode()
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=not TEST_MODE)
