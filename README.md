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

Run the application with the `--refresh` flag to download the latest TF2 schema,
`items_game.txt` and all Autobot schema properties:

```bash
python app.py --refresh
```

The files are stored under `cache/` and include `tf2_schema.json`,
`items_game.txt`, `items_game.json` and all Autobot API responses. Start
the server normally without `--refresh` after the update completes.

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
