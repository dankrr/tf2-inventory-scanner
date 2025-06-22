
import os
import re
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAMWEB_KEY = os.getenv("STEAMWEB_KEY")

def resolve_and_filter_ids(raw_text):
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    unique = []
    for l in lines:
        if l not in unique:
            unique.append(l)
    resolved = []
    for identifier in unique[:20]:
        sid = convert_to_steam64(identifier)
        if sid:
            resolved.append(sid)
    return resolved

def convert_to_steam64(identifier):
    # Already SteamID64
    if re.fullmatch(r"\d{17}", identifier):
        return identifier

    m = re.fullmatch(r"STEAM_[0-5]:([0-1]):(\d+)", identifier)
    if m:
        y = int(m.group(1))
        z = int(m.group(2))
        account_id = z * 2 + y
        return str(account_id + 76561197960265728)

    m = re.fullmatch(r"\[U:[0-5]:(\d+)\]", identifier)
    if m:
        account_id = int(m.group(1))
        return str(account_id + 76561197960265728)

    if not identifier.isnumeric():
        return resolve_vanity(identifier)

    return None


def resolve_vanity(vanity):
    if not STEAM_API_KEY:
        return None
    url = (
        "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key="
        f"{STEAM_API_KEY}&vanityurl={vanity}"
    )
    try:
        r = requests.get(url, timeout=5)
        data = r.json().get("response", {})
        if data.get("success") == 1:
            return str(data.get("steamid"))
    except Exception:
        pass
    return None

def fetch_inventory(steamid64):
    url = (
        "https://api.steampowered.com/IEconItems_440/GetPlayerItems/v1/?key="
        f"{STEAM_API_KEY}&steamid={steamid64}"
    )
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()["result"].get("items", [])
        if r.status_code in (400, 403):
            raise ValueError("Private inventory or API error")
    except Exception as e:
        logging.warning("Steam API failed for %s: %s", steamid64, e)

    if not STEAMWEB_KEY:
        return []
    fallback = (
        "https://www.steamwebapi.com/steam/api/inventory/"
        f"?key={STEAMWEB_KEY}&steam_id={steamid64}&app_id=440"
    )
    try:
        f = requests.get(fallback, timeout=10)
        f.raise_for_status()
        return f.json().get("items", [])
    except Exception as e:
        logging.error("steamwebapi.com failed for %s: %s", steamid64, e)
    return []

def get_profile_data(steamid64):
    url = (
        "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key="
        f"{STEAM_API_KEY}&steamids={steamid64}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        player = r.json()["response"]["players"][0]
    except Exception as e:
        logging.error("Failed to fetch profile for %s: %s", steamid64, e)
        return {}

    tf2_url = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key="
        f"{STEAM_API_KEY}&steamid={steamid64}&include_played_free_games=1"
    )
    try:
        games = (
            requests.get(tf2_url, timeout=10).json()["response"].get("games", [])
        )
    except Exception as e:
        logging.warning("Failed to fetch playtime for %s: %s", steamid64, e)
        games = []
    tf2 = next((g for g in games if g["appid"] == 440), {})
    hours = round(tf2.get("playtime_forever", 0) / 60, 1)

    return {
        "name": player.get("personaname"),
        "avatar": player.get("avatarfull"),
        "profile_url": player.get("profileurl"),
        "hours": hours
    }
