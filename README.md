# TF2 Inventory Scanner

![CI](https://github.com/dankrr/tf2-inventory-scanner/actions/workflows/ci.yml/badge.svg)

A lightweight Flask web app for exploring Team Fortress 2 inventories.

## Features

- Scan multiple Steam users at once
- Accepts SteamID64, SteamID3 and SteamID2 formats
- Resolves usernames and avatars via the Steam API
- Enriches items with backpack.tf prices
- Displays playtime and item details

See the [docs](docs/) directory for a full workflow description.

## Quick Start

1. Install dependencies
2. Copy `.env.example` to `.env` and set the API keys
3. Run the server:

```bash
python run_hypercorn.py
```

Open `http://localhost:5000` and submit Steam IDs to inspect.

## License

This project is released under an MIT Non-Commercial license. Commercial use
requires prior written consent from the maintainers.
