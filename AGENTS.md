# AGENTS.md

## 📦 Project Overview

This is a Flask-based web application that accepts multiple SteamID inputs in various formats (SteamID64, SteamID3, Vanity URLs), normalizes them, fetches TF2 inventory data, enriches it with prices from backpack.tf, and displays a visual inventory report per user.

### 👤 For each user, the app displays:
- Steam avatar
- Steam username
- TF2 playtime in hours
- TF2 item images with price (refined metal)
- Error messages for private inventories or Steam API issues

---

## 🔧 Agent Instructions

### 📥 Input Handling

- Extract only valid SteamID3 values like `[U:1:#########]` from free-form text.
- Normalize to SteamID64 for all inventory and profile operations.
- Ignore unrelated tokens (e.g., map info, account strings, invalid IDs).

### 🌐 External API Usage

- `ISteamUser/ResolveVanityURL` → Convert vanity → SteamID64
- `ISteamUser/GetPlayerSummaries` → Username, avatar, profile URL
- `IPlayerService/GetOwnedGames` → TF2 hours (`appid=440`)
- `steamcommunity.com/inventory` → Inventory fetch (no key)
- `backpack.tf/IGetPrices/v4` → Item pricing in refined metal

---

## 🧪 Testing & Debugging

- Catch and print errors for all API calls (`try/except`)
- Return `None` for inventory fetch failures (private or invalid users)
- Display `"Inventory private or Steam servers down."` in the UI if items cannot be retrieved

---

## 💻 Running the App

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export STEAM_API_KEY=your_steam_api_key
export BACKPACK_API_KEY=your_backpacktf_key

python app.py
