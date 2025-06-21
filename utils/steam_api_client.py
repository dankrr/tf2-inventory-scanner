
import requests, re, os
from dotenv import load_dotenv

load_dotenv()
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAMWEB_KEY = os.getenv("STEAMWEB_KEY")

def resolve_and_filter_ids(raw_text):
    ids = re.findall(r"(?:\bSTEAM_[0-5]:[01]:\d+\b|\[U:\d+:\d+\]|\d{17}|\w+)", raw_text)
    return [convert_to_steam64(x) for x in ids]

def convert_to_steam64(identifier):
    return identifier  # Placeholder for full conversion logic

def fetch_inventory(steamid64):
    url = f"https://api.steampowered.com/IEconItems_440/GetPlayerItems/v1/?key={STEAM_API_KEY}&steamid={steamid64}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["result"]["items"]
    fallback = f"https://www.steamwebapi.com/steam/api/inventory/?key={STEAMWEB_KEY}&steam_id={steamid64}&app_id=440"
    f = requests.get(fallback)
    f.raise_for_status()
    return f.json()["items"]

def get_profile_data(steamid64):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={STEAM_API_KEY}&steamids={steamid64}"
    r = requests.get(url).json()
    player = r["response"]["players"][0]

    tf2_url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={STEAM_API_KEY}&steamid={steamid64}&include_played_free_games=1"
    games = requests.get(tf2_url).json()["response"].get("games", [])
    tf2 = next((g for g in games if g["appid"] == 440), {})
    hours = round(tf2.get("playtime_forever", 0) / 60, 1)

    return {
        "name": player.get("personaname"),
        "avatar": player.get("avatarfull"),
        "profile_url": player.get("profileurl"),
        "hours": hours
    }
