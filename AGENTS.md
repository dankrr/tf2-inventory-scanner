# AGENTS.md

## 🧠 Project Summary

This is a Python Flask web application that allows a user to input one or more Steam IDs in various formats. The app resolves each ID to a SteamID64, fetches the user’s TF2 inventory, enriches it with item prices from backpack.tf, and displays the following:

- Steam username
- Steam avatar (clickable, linking to profile)
- TF2 playtime (in hours)
- Item names, images, and backpack.tf prices
- Error handling for private inventories or Steam downtime

---

## 📦 Agent Modules

The repository currently exposes several entry points:

1. **`app.py`** – the Flask web application for scanning multiple Steam users.
2. **`inventory_scanner.py`** – a small command-line tool that fetches the
   inventory for a single SteamID.
3. **`utils/steam_api_client.py`** – common helpers for Steam Web API requests.
4. **`utils/inventory_processor.py`** – utilities that enrich and sort inventory
   data.
5. **`utils/schema_fetcher.py`** – caches the TF2 item schema for other modules.

To register a new scanning agent, place its module under `utils/` (or create a
new top-level script) and add any reusable functions to `utils/__init__.py`.
Update tests and documentation accordingly, then run `pre-commit` before
submitting a pull request.

---

## 🔍 Expected Steam ID Formats

Input may include:
- SteamID64 (17-digit numeric)
- SteamID2 (e.g., `STEAM_0:1:123456`)
- SteamID3 (e.g., `[U:1:123456]`)
- Vanity URLs (e.g., `gaben`)
- Mixed `status` dumps from TF2 servers

### ✅ Parsing Rules:
- Only accept `[U:1:########]` from TF2 status output
- Ignore `[A:1:...]`, `map:`, usernames, or lines without valid IDs
- Convert everything to SteamID64 before processing

Use `ResolveVanityURL` or manual conversion logic as needed.

---

## 🌐 External API Requirements

### 🔑 Steam API (requires STEAM_API_KEY):
- `ISteamUser/ResolveVanityURL` – for vanity → SteamID64
- `ISteamUser/GetPlayerSummaries` – get username, avatar, profile URL
- `IPlayerService/GetOwnedGames` – extract TF2 playtime (appid 440)

### 🎒 Steam Inventory:
- `https://steamcommunity.com/inventory/{steamid}/440/2`
  - No API key required
  - Fails for private accounts or invalid SteamIDs

### 💰 backpack.tf API (requires BACKPACK_API_KEY):
- `https://backpack.tf/api/IGetPrices/v4?key=<BACKPACK_API_KEY>`
  - Get prices by item name
  - Return values in refined metal (e.g., `5.33 ref`)

### 📜 Steam Item Schema API:
- `https://api.steampowered.com/IEconItems_440/GetSchema/v1/?key=<STEAM_API_KEY>`
  - Used by `schema_fetcher.py` to cache item metadata

---

## 💻 Flask Application Behavior

1. User submits one or more Steam IDs in a form
2. App parses and filters valid IDs
3. For each user:
   - Resolves SteamID
   - Fetches profile summary and TF2 hours
   - Fetches inventory and item prices
4. Displays a panel per user:
   - Avatar (clickable)
   - Username
   - Playtime (in hours)
   - Item cards with image, name, and price
   - If inventory fetch fails, show `"Inventory private or Steam servers down."`

---

## ⚙️ Development Guide

- Structure all logic in `app.py`
- Template in `templates/index.html`
- Do **not modify** `static/` or unrelated template files
- Use `requests` with timeouts and error handling
- Raise `ValueError` early if required API keys are missing
- Cache `prices` during each POST cycle to avoid duplicate fetches

---

## ✨ Style & Formatting Rules

- Use `black` for formatting Python files
- Use `Jinja2` for HTML with simple loops and conditions
- Use `<img>` width `64` for avatars and `32` for items
- Profile links should open in a new tab
- Always use HTTPS endpoints where available

---

## 🧪 Testing

- Simulate TF2 `status` output as multiline input
- Gracefully handle:
  - Invalid Steam IDs
  - Private inventories
  - Missing keys
- Return an empty inventory list + error message if fetch fails

---

## 🔐 Security

- Do not expose API keys in HTML or client-side
- Always use `os.getenv()` to access keys
- Show fallback UI if keys are missing (e.g., “API keys required to run”)

---

## 📌 Goals for Codex

- Maintain clear separation between input parsing, data fetching, and rendering
- Add modular improvements (e.g., pagination, sorting) without breaking layout
- Allow future extensions like downloadable inventory reports or filtering

## ✅ Contributor Setup

All contributors must install and run `pre-commit` to ensure code
is formatted, linted, and scanned for secrets.

---

## 📖 Role of This Document

`AGENTS.md` acts as a central style and architecture guide for both humans and
any Codex automation working on this repository. It outlines accepted Steam ID
formats, required APIs, and coding conventions. Use it when extending the
project or adding new modules to ensure consistency across contributions.


