# TF2 Inventory Scanner ![CI](https://github.com/dankrr/tf2-inventory-scanner/actions/workflows/ci.yml/badge.svg)

## Overview

This Flask app scans the Team Fortress 2 inventories for one or more Steam users. It accepts **SteamID64**, **SteamID3**, **SteamID2**, and **vanity URLs**, resolves them to 64-bit IDs and enriches inventory data with the Steam Web API and cached item schema.

![User panel screenshot](docs/images/user_panel.png)

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt -r requirements-test.txt
   ```
2. Copy `.env.example` and set `STEAM_API_KEY`:
   ```bash
   cp .env.example .env
   # edit .env and set STEAM_API_KEY=<your key>
   ```
   Environment variables are loaded with **python-dotenv**.

## Usage

Run the app locally and open `http://localhost:5000` in your browser:
```bash
python app.py
```
Submit any supported SteamID (SteamID64, SteamID3, SteamID2, or vanity URL). Each user panel shows the avatar, TF2 playtime, and an item grid.

## Development

- Templates live under `templates/`.
- The TF2 item schema is cached automatically; refresh it with:
  ```bash
  python app.py --refresh
  ```
- Use `--test` to load a cached inventory for offline mode.

## Testing

Run formatting and tests:
```bash
pre-commit run --all-files
pytest --cov=utils --cov=app
```
HTML coverage reports are written to `htmlcov/`.

## Docker / Deployment

Build and run a container locally:
```bash
docker build -t tf2-scanner .
docker run -p 5000:5000 tf2-scanner
```
The server can also be accessed on your LAN.
