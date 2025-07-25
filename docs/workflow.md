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

Cached schema and price files live under the `cache/` directory. Run

```bash
python run.py --refresh --verbose
```

to update these files before starting the server.

## APIs Used

- **ISteamUser/ResolveVanityURL** – convert vanity names to SteamID64
- **ISteamUser/GetPlayerSummaries** – fetch username and avatar
- **IPlayerService/GetOwnedGames** – obtain TF2 playtime
- **IEconItems_440/GetPlayerItems** – retrieve inventory contents
- **backpack.tf/IGetPrices** – map item names to prices
- **schema.autobot.tf** – download item schema information

## Data Pipeline

1. Input IDs are normalised to SteamID64.
2. Profile and playtime information is fetched using the Steam Web API.
3. The inventory API returns raw item data.
4. Item attributes are enriched using the cached schema and prices.
5. The resulting items are rendered in the browser with images and values.
