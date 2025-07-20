import os
import re
import asyncio
import time
import json
import argparse
import psutil
import sys
import contextlib
from pathlib import Path
from typing import List, Dict, Any
from types import SimpleNamespace

from dotenv import load_dotenv
from quart import Quart, render_template, request, flash, jsonify
import socketio
from hypercorn.asyncio import serve
from hypercorn.config import Config
from utils.steam_api_client import extract_steam_ids
import utils.inventory_processor as ip

from utils import steam_api_client as sac
from utils import local_data
from utils import constants as consts
from utils.price_loader import ensure_prices_cached, ensure_currencies_cached
from utils.cache_manager import _do_refresh, fetch_missing_cache_files

COLOR_YELLOW = "\033[33m"
COLOR_RESET = "\033[0m"

load_dotenv()
# ENABLE_SECRET=true  # enable sessions (default)
# SECRET_KEY=mysecret # optional, defaults to "dev-secret-key"
if not os.getenv("STEAM_API_KEY"):
    raise ValueError(
        "Required env var missing: STEAM_API_KEY. Make sure you have a .env file or export it."
    )

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--refresh", action="store_true")
parser.add_argument("--verbose", action="store_true")
parser.add_argument("--test", action="store_true")
ARGS, _ = parser.parse_known_args()


if ARGS.refresh:
    try:
        loop = asyncio.get_running_loop()
        loop.run_until_complete(_do_refresh())
    except RuntimeError:
        asyncio.run(_do_refresh())
    raise SystemExit(0)


TEST_MODE = ARGS.test
TEST_STEAMID: str = ""
TEST_INVENTORY_RAW: Dict[str, Any] | None = None
TEST_INVENTORY_STATUS: str = ""
TEST_API_RESULTS_DIR: Path | None = None

STEAM_API_KEY = os.environ["STEAM_API_KEY"]

app = Quart(__name__, static_folder=None)
app.config.setdefault("PROVIDE_AUTOMATIC_OPTIONS", True)
app.static_folder = "static"
app.add_url_rule("/static/<path:filename>", "static", app.send_static_file)

enable_secret = os.getenv("ENABLE_SECRET", "true").lower() == "true"
if enable_secret:
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
else:
    print("\u26a0 Sessions are disabled because ENABLE_SECRET=false", flush=True)

# Socket.IO runs in ASGI mode with Quart.
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socketio = socketio.ASGIApp(sio, other_asgi_app=app)
# Exported ASGI application used by run.py
asgi_app = socketio

MAX_MERGE_MS = 0
local_data.load_files(auto_refetch=True, verbose=ARGS.verbose)
_prices_path = ensure_prices_cached(refresh=ARGS.refresh)
if _prices_path.exists() and _prices_path.stat().st_size <= 2:
    print(
        f'{COLOR_YELLOW}⚠ Pricing unavailable (using empty cache). Inventories will show "Price: N/A".{COLOR_RESET}'
    )
_currencies_path = ensure_currencies_cached(refresh=ARGS.refresh)
try:
    with open(_currencies_path) as f:
        local_data.CURRENCIES = json.load(f)["response"]["currencies"]
except Exception:
    local_data.CURRENCIES = {}

# --- Utility functions ------------------------------------------------------

IGNORED_STACK_KEYS = {
    "level",
    "custom_description",
    "custom_name",
    "origin",
    "id",
    "original_id",
    "inventory",
}

# Item names that should never be merged into quantity stacks
UNSTACKABLE_NAMES = {
    "Killstreak Kit",
    "Specialized Killstreak Kit",
    "Professional Killstreak Kit",
    "Killstreak Kit Fabricator",
}


def kill_process_on_port(port: int) -> None:
    """Terminate any process currently listening on ``port``."""

    for conn in psutil.net_connections(kind="tcp"):
        if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
            pid = conn.pid
            if pid and pid != os.getpid():
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    proc = psutil.Process(pid)
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        proc.kill()


def stack_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return ``items`` grouped into quantity stacks.

    Items whose ``name`` or ``item_type_name`` appears in
    :data:`UNSTACKABLE_NAMES` are kept separate.  All other items are merged by
    comparing every field except those in :data:`IGNORED_STACK_KEYS`.
    """

    grouped: Dict[str, Dict[str, Any]] = {}
    uniques: List[Dict[str, Any]] = []

    for itm in items:
        if not isinstance(itm, dict):
            continue

        item_name = itm.get("name")
        item_type = itm.get("item_type_name")
        if item_name in UNSTACKABLE_NAMES or item_type in UNSTACKABLE_NAMES:
            new_item = itm.copy()
            new_item.setdefault("quantity", 1)
            uniques.append(new_item)
            continue

        key_obj = {k: v for k, v in itm.items() if k not in IGNORED_STACK_KEYS}
        try:
            key = json.dumps(key_obj, sort_keys=True)
        except TypeError:
            key = str(key_obj)

        if key in grouped:
            grouped[key]["quantity"] += 1
        else:
            new_item = itm.copy()
            new_item.setdefault("quantity", 1)
            grouped[key] = new_item

    return list(grouped.values()) + uniques


async def get_player_summary(steamid64: str) -> Dict[str, Any] | None:
    """Return profile name, avatar URL and TF2 playtime for a user.

    Returns ``None`` if the player summary could not be retrieved.
    """
    print(f"Fetching player summary for {steamid64}")
    players: List[Dict[str, Any]] | None = None
    playtime: float | None = None

    if TEST_MODE and steamid64 == TEST_STEAMID:
        api_dir = Path("cached_inventories") / steamid64 / "api_results"
        summary_file = api_dir / "player_summaries.json"
        playtime_file = api_dir / "playtime.json"

        if summary_file.exists():
            try:
                with summary_file.open() as f:
                    players = json.load(f)
            except Exception:
                players = None
        if playtime_file.exists():
            try:
                with playtime_file.open() as f:
                    playtime = json.load(f)
            except Exception:
                playtime = None

        if players is None or playtime is None:
            players = await sac.get_player_summaries_async([steamid64])
            playtime = await sac.get_tf2_playtime_hours_async(steamid64)
            api_dir.mkdir(parents=True, exist_ok=True)
            with summary_file.open("w") as f:
                json.dump(players, f)
            with playtime_file.open("w") as f:
                json.dump(playtime, f)
    else:
        players = await sac.get_player_summaries_async([steamid64])
        playtime = await sac.get_tf2_playtime_hours_async(steamid64)

    if not players:
        return None

    player = players[0]
    profile = player.get(
        "profileurl", f"https://steamcommunity.com/profiles/{steamid64}"
    )
    username = player.get("personaname", steamid64)
    avatar = player.get("avatarfull", "")

    return {
        "username": username,
        "avatar": avatar,
        "playtime": round(playtime, 1),
        "profile": profile,
    }


async def fetch_inventory(steamid64: str) -> Dict[str, Any]:
    """Fetch TF2 inventory items for a user and return items with a status."""
    global TEST_INVENTORY_RAW, TEST_INVENTORY_STATUS

    if TEST_MODE and steamid64 == TEST_STEAMID and TEST_INVENTORY_RAW is not None:
        status = TEST_INVENTORY_STATUS or "parsed"
        data = TEST_INVENTORY_RAW
    else:
        status, data = await sac.fetch_inventory_async(steamid64)
    items: List[Dict[str, Any]] = []
    if status == "parsed":
        try:
            items = ip.process_inventory(
                data, valuation_service=ip.get_valuation_service()
            )
        except Exception:
            app.logger.exception("Failed to enrich inventory for %s", steamid64)
            status = "failed"
            items = []
    return {"items": items, "status": status}


async def build_user_data_async(steamid64: str) -> Dict[str, Any] | None:
    """Asynchronously build user card data.

    Returns ``None`` if the user summary could not be retrieved.
    """
    t1 = time.perf_counter()
    summary_task = asyncio.create_task(get_player_summary(steamid64))
    inv_task = asyncio.create_task(fetch_inventory(steamid64))
    summary, inv_result = await asyncio.gather(summary_task, inv_task)
    if summary is None:
        return None
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


def normalize_user_payload(user: Dict[str, Any]) -> SimpleNamespace:
    """Return a namespace with ``items`` guaranteed to be a list."""

    items = user.get("items", [])
    user["items"] = items if isinstance(items, list) else []
    return SimpleNamespace(**user)


async def fetch_and_process_single_user(steamid64: int) -> str:
    user = await build_user_data_async(str(steamid64))
    user = normalize_user_payload(user)
    return await render_template("_user.html", user=user)


async def fetch_and_process_many(ids: List[str]) -> tuple[List[str], List[str]]:
    """Return rendered user cards and a list of IDs that failed."""

    unique_ids = list(dict.fromkeys(str(s) for s in ids))

    tasks: Dict[str, asyncio.Task] = {
        sid: asyncio.create_task(build_user_data_async(sid)) for sid in unique_ids
    }

    results = await asyncio.gather(*tasks.values())
    html_snippets: List[str] = []
    failed_ids: List[str] = []
    seen: set[str] = set()

    for _, user in zip(unique_ids, results):
        if not user or not isinstance(user, dict):
            continue
        if not user.get("username") and not user.get("personaname"):
            continue
        user_ns = normalize_user_payload(user)
        if user_ns.steamid in seen:
            print("DUPLICATE PANEL:", user_ns.steamid)
            continue
        seen.add(user_ns.steamid)
        if user_ns.status == "failed":
            failed_ids.append(user_ns.steamid)
        html_snippets.append(await render_template("_user.html", user=user_ns))

    return html_snippets, failed_ids


async def _setup_test_mode() -> None:
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
    api_dir = cache_dir / steamid / "api_results"
    api_dir.mkdir(parents=True, exist_ok=True)
    global TEST_API_RESULTS_DIR
    TEST_API_RESULTS_DIR = api_dir
    inv_api_file = api_dir / "inventory.json"
    summary_file = api_dir / "player_summaries.json"
    playtime_file = api_dir / "playtime.json"

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
        status, data = await sac.fetch_inventory_async(steamid)
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

    # save inventory API result
    with inv_api_file.open("w") as f:
        json.dump(TEST_INVENTORY_RAW, f)

    if summary_file.exists():
        with summary_file.open() as f:
            summary_data = json.load(f)
    else:
        summary_data = await sac.get_player_summaries_async([steamid])
        with summary_file.open("w") as f:
            json.dump(summary_data, f)

    if playtime_file.exists():
        with playtime_file.open() as f:
            playtime_data = json.load(f)
    else:
        playtime_data = await sac.get_tf2_playtime_hours_async(steamid)
        with playtime_file.open("w") as f:
            json.dump(playtime_data, f)

    TEST_STEAMID = steamid
    user = normalize_user_payload(await build_user_data_async(steamid))
    app.config["PRELOADED_USERS"] = [user]
    app.config["TEST_STEAMID"] = steamid


@sio.on("start_fetch", namespace="/inventory")
async def handle_start_fetch(sid: str, data: Dict[str, Any]) -> None:
    """Stream inventory items for a single Steam user."""

    steamid = data.get("steamid") if isinstance(data, dict) else None
    if not isinstance(steamid, str):
        await sio.emit(
            "done",
            {"steamid": steamid, "status": "invalid"},
            to=sid,
            namespace="/inventory",
        )
        return
    try:
        steamid64 = sac.convert_to_steam64(steamid)
    except ValueError:
        await sio.emit(
            "done",
            {"steamid": steamid, "status": "invalid"},
            to=sid,
            namespace="/inventory",
        )
        return

    status, raw = await sac.fetch_inventory_async(steamid64)
    if status != "parsed":
        await sio.emit(
            "done",
            {"steamid": steamid64, "status": status},
            to=sid,
            namespace="/inventory",
        )
        return

    total = len(raw.get("items") or [])
    await sio.emit(
        "info", {"steamid": steamid64, "total": total}, to=sid, namespace="/inventory"
    )

    if not local_data.ITEMS_BY_DEFINDEX:
        await fetch_missing_cache_files()
        local_data.load_files(auto_refetch=False)

    processed = 0
    async for item in ip.process_inventory_streaming(raw):
        item["steamid"] = steamid64
        await sio.emit("item", item, to=sid, namespace="/inventory")
        await asyncio.sleep(0)
        processed += 1
        await sio.emit(
            "progress",
            {"steamid": steamid64, "processed": processed, "total": total},
            to=sid,
            namespace="/inventory",
        )
        # Yield so Hypercorn flushes events between iterations
        await asyncio.sleep(0.01)

    await sio.emit(
        "done", {"steamid": steamid64, "status": status}, to=sid, namespace="/inventory"
    )


@app.post("/retry/<int:steamid64>")
async def retry_single(steamid64: int):
    """Reprocess a single user and return a rendered snippet."""
    return await fetch_and_process_single_user(steamid64)


@app.post("/api/users")
async def api_users():
    """Return rendered user cards for multiple Steam IDs."""

    payload = await request.get_json(silent=True) or {}
    ids_raw = payload.get("ids", [])
    if not isinstance(ids_raw, list):
        return jsonify({"error": "ids must be a list"}), 400

    try:
        ids = [sac.convert_to_steam64(str(i)) for i in ids_raw]
    except ValueError:
        return jsonify({"error": "Invalid Steam ID"}), 400

    snippets, _ = await fetch_and_process_many(ids)
    return jsonify({"html": snippets})


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
async def index():
    users: List[Dict[str, Any]] = []
    steamids_input = ""
    ids: List[str] = []
    invalid: List[str] = []
    failed_ids: List[str] = []
    if request.method == "GET" and app.config.get("PRELOADED_USERS"):
        users = app.config.get("PRELOADED_USERS", [])
        steamids_input = app.config.get("TEST_STEAMID", "")
        failed_ids = [u.steamid for u in users if getattr(u, "status", "") == "failed"]
    if request.method == "POST":
        form = await request.form
        steamids_input = form.get("steamids", "")
        tokens = re.split(r"\s+", steamids_input.strip())
        raw_ids = extract_steam_ids(steamids_input)
        invalid = [t for t in tokens if t and t not in raw_ids]
        ids = [sac.convert_to_steam64(t) for t in raw_ids]
        print(f"Parsed {len(ids)} valid IDs, {len(invalid)} tokens ignored")
        if ids:
            if invalid and app.secret_key:
                await flash(f"Ignored {len(invalid)} invalid input(s).")
            users, failed_ids = await fetch_and_process_many(ids)
        else:
            if app.secret_key:
                await flash(
                    "No valid Steam IDs found. Please input in SteamID64, SteamID2, or SteamID3 format."
                )
            return await render_template(
                "index.html",
                users=users,
                steamids=steamids_input,
                ids=[],
                failed_ids=[],
            )
    return await render_template(
        "index.html",
        users=users,
        steamids=steamids_input,
        ids=ids,
        failed_ids=failed_ids,
        debug_ms=MAX_MERGE_MS if os.getenv("FLASK_DEBUG") else None,
    )


if __name__ == "__main__":

    async def _main() -> None:
        print(
            "\N{LEFT-POINTING MAGNIFYING GLASS} Validating schema and pricing cache..."
        )
        ok, refreshed, schema_refreshed = await fetch_missing_cache_files()
        if not ok:
            print("\N{CROSS MARK} Could not fetch required schema. Exiting.")
            raise SystemExit(1)
        # Reload schema now that it's guaranteed to exist
        local_data.load_files(auto_refetch=False)
        if schema_refreshed and not TEST_MODE:
            print(
                f"{COLOR_YELLOW}🔄 Restarting to load updated schema...{COLOR_RESET}",
                flush=True,
            )
            os.execv(sys.executable, [sys.executable] + sys.argv)

        port = int(os.getenv("PORT", 5000))
        kill_process_on_port(port)
        if TEST_MODE:
            await _setup_test_mode()
        config = Config()
        config.bind = [f"0.0.0.0:{port}"]
        config.use_reloader = not TEST_MODE
        await serve(asgi_app, config)

    asyncio.run(_main())
