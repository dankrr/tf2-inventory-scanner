# TF2 Inventory Scanner


A lightweight Flask web app for exploring Team Fortress 2 inventories.

## Features

- Scan multiple Steam users at once
- Accepts SteamID64, SteamID3 and SteamID2 formats
- Resolves usernames and avatars via the Steam API
- Enriches items with backpack.tf prices
- Displays playtime and item details
- Refreshes local schema and price caches with a command-line flag
- Capture API data to disk with `--test` for offline development

See the [docs](docs/) directory for a full workflow description.

## Quick Start

1. Install dependencies
2. Copy `.env.example` to `.env` and set the API keys
3. (Optional) Refresh item schema and prices:

```bash
python run.py --refresh
```

4. (Optional) Start in test mode to reuse cached API data:

```bash
python run.py --test
```

5. Run the server:

```bash
python run.py
```

Open `http://localhost:5000` and submit Steam IDs to inspect.

## Docker

```bash
docker build -t tf2scanner .
docker run --env-file .env -p 5000:5000 tf2scanner
```

## License

This project is released under an MIT Non-Commercial license. Commercial use
requires prior written consent from the maintainers.
