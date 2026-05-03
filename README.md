# TF2 Inventory Scanner

A lightweight Flask web app for exploring Team Fortress 2 inventories.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT%20Non--Commercial-lightgrey)

---

## Features

- Scan multiple Steam users simultaneously
- Accepts SteamID64, SteamID2, SteamID3, vanity URLs, and raw `status` dumps from TF2 servers
- Resolves usernames and avatars via the Steam API
- Enriches items with backpack.tf prices (refined metal values)
- Detects item qualities (Unusual, Strange, Haunted, etc.) and unusual effects
- Displays wear tiers, killstreak tiers, sheens, paint colors, and spells
- Shows TF2 playtime per user
- Groups duplicate items into quantity stacks automatically
- Refreshes local schema and price caches via a command-line flag
- Captures live API responses to disk with `--test` for fully offline development

See the [docs/](docs/) directory for detailed workflow and architecture documentation.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ (3.12 recommended) |
| pip | bundled with Python |
| Git | optional, to clone the repo |

On Linux/macOS the commands below use `python3`. On Windows use `python` and `Scripts\` instead of `bin/`.

---

## Setup (Local Development)

```bash
# 1. Clone
git clone https://github.com/dankrr/tf2-inventory-scanner.git
cd tf2-inventory-scanner

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env        # Edit with your API keys (see below)

# 5. Start the app
python run.py
```

Then open: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the required keys:

```ini
# Required
STEAM_API_KEY=your_steam_key_here
BPTF_API_KEY=your_backpack_tf_key_here

# Optional
BACKPACK_TF_API_KEY=      # Alias for BPTF_API_KEY (legacy setups)
FLASK_SECRET_KEY=replace_with_random_secret
CACHE_RETRIES=2            # Retries when fetching remote caches
CACHE_DELAY=2              # Seconds between retry attempts
SKIP_CACHE_INIT=0          # Set to 1 to skip cache validation on startup
CDN_RESOLVER_ENABLED=1     # Set to 0 to disable Steam CDN variant image lookups
```

**Getting API keys:**
- Steam API key: [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
- backpack.tf API key: [https://backpack.tf/developer/apikey/view](https://backpack.tf/developer/apikey/view)

---

## Common Tasks

### Refresh item schema and prices
```bash
python run.py --refresh
```
Also clears `cache/cdn_images.json` so variant CDN icons can be re-resolved with fresh market data.

### Run in test mode (reuse cached API data)
```bash
python run.py --test
```
Test mode prompts for a SteamID64 on startup, fetches and caches that user's inventory, then serves all subsequent requests from disk — no live API calls needed.

### Activate / deactivate the virtual environment
```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
deactivate
```

---

## Running Tests

```bash
pip install -r requirements-test.txt
pytest
```

Pre-commit hooks (formatting, linting, secret scanning) run automatically on commit once installed:

```bash
pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor workflow.

---

## Docker

```bash
docker build -t tf2scanner .
docker run -d --name tf2scanner --env-file .env -p 5000:5000 tf2scanner
```

See [docs/docker.md](docs/docker.md) for additional container configuration options.

---

## Documentation

| Doc | Description |
|---|---|
| [docs/overview.md](docs/overview.md) | Architecture and file descriptions |
| [docs/workflow.md](docs/workflow.md) | How the scanner processes users end-to-end |
| [docs/refresh.md](docs/refresh.md) | Updating schema and price caches |
| [docs/test_mode.md](docs/test_mode.md) | Offline development with captured API data |
| [docs/docker.md](docs/docker.md) | Running the app in Docker |
| [docs/exclusions.md](docs/exclusions.md) | Configuring hidden item origins |
| [docs/CACHE_AND_PRICING.md](docs/CACHE_AND_PRICING.md) | Price data fault tolerance |

---

## License

Released under the MIT Non-Commercial License. Commercial use requires prior written consent from the maintainers.

---

## Author

Created by [dankrr](https://steamcommunity.com/id/dankrr/).
