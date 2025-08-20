# TF2 Inventory Scanner

A lightweight Flask web app for exploring Team Fortress 2 inventories.

---

## Features

- Scan multiple Steam users at once
- Accepts SteamID64, SteamID3 and SteamID2 formats
- Resolves usernames and avatars via the Steam API
- Enriches items with backpack.tf prices
- Displays playtime and item details
- Refreshes local schema and price caches with a command-line flag
- Capture API data to disk with `--test` for offline development

See the [docs](docs/) directory for a full workflow description.

---

## Prerequisites

- **Python**: 3.10+ (3.12 recommended)
- **pip**: bundled with Python
- (Optional) **Git**: to clone and manage the repo

On Linux/macOS, commands below use `python3`.  
On Windows, use `python` and `Scripts\\` instead of `bin/` where noted.

---

## Setup (Local Development)

```bash
# 1) Clone
git clone https://github.com/dankrr/tf2-inventory-scanner.git
cd tf2-inventory-scanner

# 2) Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) Upgrade pip & install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4) Configure environment
cp .env.example .env         # Then edit with your API keys

# 5) Run the app
python run.py                # or: python app.py
```

Then open: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Environment Variables (`.env`)

Create a `.env` file in the project root:

```ini
# Server
HOST=127.0.0.1
PORT=5000
FLASK_ENV=development
FLASK_DEBUG=1

# Steam / TF2
STEAM_API_KEY=your_steam_web_api_key
# STEAM_API_BASE=https://api.steampowered.com

# Backpack.tf (optional pricing)
# BACKPACKTF_API_KEY=your_backpacktf_key
# BACKPACKTF_BASE=https://backpack.tf/api

# Caching
CACHE_DIR=./cache
SCHEMA_CACHE_PATH=./cache/schema.json
```

---

## Common Tasks

### Refresh item schema and prices
```bash
python run.py --refresh
```

### Start in test mode to reuse cached API data
```bash
python run.py --test
```

### Activate / deactivate venv
```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
deactivate
```

---

## Docker

```bash
docker build -t tf2scanner .
docker run -d --name tf2scanner --env-file .env -p 5000:5000 tf2scanner
```

---

## License

This project is released under an MIT Non-Commercial license.  
Commercial use requires prior written consent from the maintainers.

---

## Author

This project was created by [dankrr](https://steamcommunity.com/id/dankrr/).
