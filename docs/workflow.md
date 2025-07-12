# Application Workflow

This document explains how the TF2 Inventory Scanner processes each request.

## 1. Input
- Users submit one or more Steam IDs.
- SteamID64, SteamID3, SteamID2 and vanity URLs are accepted.

## 2. Resolution and Profiles
- Every ID is converted to a SteamID64 using the Steam API.
- The app fetches profile details such as display name and avatar.

## 3. Inventory Fetching
- The TF2 inventory API is queried for each user.
- Private or empty inventories are reported with an error message.

## 4. Enrichment
- Item data is enriched with information from cached schema files.
- Prices are looked up from a local map built from backpack.tf data.

## 5. Output
- For each user the page shows the avatar, playtime and a grid of items.
- Item cards list the name, image and price.

All network calls are performed asynchronously with `httpx.AsyncClient` to
fetch multiple users in parallel.

## Refreshing Data

The combined Steam schema is stored at `data/schema_steam.json` and is refreshed
automatically if older than 24 hours. Price files remain under the `cache/`
directory. Run

```bash
python app.py --refresh --verbose
```

to update these files before starting the server.

## Item Title Precedence

When rendering an item card or modal the scanner builds the title using the
first available value from the following fields:

```
composite_name > display_base > resolved_name > base_name > display_name > name
```

Decorated weapons and war‑paint tools often set a `composite_name` combining
paintkit and weapon name. This field always takes priority when present so
skins display their full painted name. War‑paint tools follow the same rule,
showing `Warhawk Rocket Launcher`-style names whenever possible.

## Paintkit Schema Names

Steam's schema occasionally lists decorated weapons or war-paint tools with
placeholder names such as `"Paintkitweapon"` or `"Paintkittool"`. The scanner
skips these placeholders. When detected, it uses the item's `composite_name` if
present or falls back to the target weapon name so skins display the correct
weapon title.
