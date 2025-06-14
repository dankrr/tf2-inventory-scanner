# TF2 Inventory Web App

This project provides a small Flask application for inspecting the Team Fortress
2 inventory of one or more Steam users. The app scans pasted server output for
SteamID3 tokens such as `[U:1:123456]` and converts them to SteamID64 by adding
`76561197960265728` to the account ID.
It also shows each player's Steam profile name, avatar, and total time spent in
TF2.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` to set your credentials:

```
STEAM_API_KEY=your_steam_key
BACKPACK_API_KEY=your_backpack_key
```

The application uses **python-dotenv** to load these values at runtime.

## Usage

```bash
python app.py
```

Navigate to `http://localhost:5000` and paste text containing SteamID3 tokens
(for example from the in-game `status` command). The app will display each
user's avatar, profile name, TF2 playtime, and a list of TF2 items with icons
and prices in refined metal.

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

The application converts the ID to SteamID64, fetches the inventory, and looks
up prices via backpack.tf.
