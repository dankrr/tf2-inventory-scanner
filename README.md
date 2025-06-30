# TF2 Inventory Web App ![CI](https://github.com/dankrr/tf2-inventory-scanner/actions/workflows/ci.yml/badge.svg) ![coverage](https://img.shields.io/badge/coverage-unknown-lightgrey.svg)

This project provides a small Flask application for inspecting the Team Fortress
2 inventory of one or more Steam users. It accepts SteamIDs in several formats
(SteamID64, SteamID2, SteamID3 or vanity URLs) separated by spaces, commas or newlines.
The app converts everything to SteamID64 before fetching profile and inventory data.
It also shows each player's Steam profile name, avatar, and total time spent in
TF2.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Quick start

Run the Flask server locally:

```bash
export FLASK_DEBUG=1
python app.py
```

To run the tests with cached data:

```bash
export STEAM_API_KEY=XXX
export TEST_STEAM_ID=76561197972495328
python scripts/fetch_data.py
pytest -q
```

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` to set your credentials:

```
STEAM_API_KEY=your_steam_key
```

The application uses **python-dotenv** to load these values at runtime.

## Running locally

```bash
cp .env.example .env   # then edit keys
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Usage

```bash
python app.py
```

Navigate to `http://localhost:5000` and paste text containing one or more
SteamIDs (any supported format). The app will display each user's avatar,
profile name, TF2 playtime, and a list of TF2 items with icons.

## Example

```
#    431 "Bread"             [U:1:1602028086]    00:48       83    0 active
steamid : [A:1:903510047:45685] (90268209031837727)
account : not logged in  (No account specified)
tags    : ctf,hidden
map     : ctf_doublecross at: 0 x, 0 y, 0 z
```

Only the SteamID3 token is used:

```
[U:1:1602028086]
```

The application converts the ID to SteamID64 and fetches the inventory.

## Dependency Management

Dependencies are pinned in `requirements.txt` and locked with
`requirements.lock`. To update packages securely:

```bash
pip install -r requirements.txt --upgrade
pip-compile --generate-hashes -o requirements.lock requirements.txt
pip-audit
```

Always run `pip-audit` to check for known vulnerabilities after upgrading.

### Lint & Test

```bash
ruff check .
black --check .
pytest --cov=utils --cov=app
```

The HTML coverage report is written to `htmlcov/`.

### Pre-commit

Install hooks once:

```bash
pre-commit install
```

### Updating item cache

Run the application with the `--refresh` flag to download the latest TF2 schema
and `items_game.txt`:

```bash
python app.py --refresh
```

The files are stored under `cache/` as `tf2_schema.json`, `items_game.txt` and
`items_game_cleaned.json`. Start the server normally without `--refresh` after
the update completes.

### Fetching example data

Use the helper script below to download raw schema files and a sample
inventory for testing. `STEAM_API_KEY` and `TEST_STEAM_ID` must be set in your
environment:

```bash
python scripts/fetch_data.py
```

### Deploy

The app can be deployed to any platform that supports Python 3.12. For Docker:

```bash
docker build -t tf2-scanner .
docker run -p 5000:5000 tf2-scanner
```

### LAN testing

```bash
python app.py          # now reachable at http://<LAN_IP>:5000
docker run -p 5000:5000 tf2-inv
```

## 🎖 Enriched Item Fields

| Key                 | Example                        | Description           |
| ------------------- | ------------------------------ | --------------------- |
| defindex            | `222`                          | Item definition index |
| name                | `Professional Rocket Launcher` | Display name          |
| quality             | `Unique`                       | Item quality string   |
| quality_color       | `#FFD700`                      | Hex color for quality |
| image_url           | `https://...`                  | Item icon URL         |
| item_type_name      | `Rocket Launcher`              | Type from schema      |
| item_name           | `Rocket Launcher`              | Raw schema name       |
| craft_class         | `weapon`                       | Craft class           |
| craft_material_type | `weapon`                       | Craft material        |
| item_set            | _varies_                       | Item set name         |
| capabilities        | _dict_                         | Capability flags      |
| tags                | _list_                         | Schema tags           |
| equip_regions       | _list_                         | Equip region list     |
| item_class          | `tf_weapon_rocketlauncher`     | Class string          |
| slot_type           | `primary`                      | Equip slot            |
| level               | `1`                            | Item level            |
| origin              | `Timed Drop`                   | Item origin           |
| killstreak_tier     | `Professional`                 | Killstreak tier       |
| sheen               | `Team Shine`                   | Killstreak sheen      |
| killstreaker        | `Fire Horns`                   | Killstreaker effect   |
| paint_name          | `A Deep Commitment to Purple`  | Applied paint         |
| paint_hex           | `#7D4071`                      | Paint color           |
| spells              | `["Exorcism"]`                 | Halloween spells      |
| spell_flags         | _dict_                         | Spell badge flags     |
| strange_parts       | `["Buildings Destroyed"]`      | Attached parts        |
| unusual_effect      | `Burning Flames`               | Unusual effect        |
| is_festivized       | `true`                         | Has festive lights    |
| custom_name         | `"My Launcher"`                | Player-set name       |
| badges              | `[{'icon': '🎨'}]`             | Badge metadata        |
| misc_attrs          | _list_                         | Unhandled attributes  |

**Emoji legend:** 🎨 paint, ⚔️ killstreak tier, 💀 killstreaker, ✨ sheen, 👣 footprints, 👻 exorcism, 🎃 pumpkin bombs, 🗣 voices from below, 📊 strange parts, 🎄 festive, 🔥 unusual effect.
