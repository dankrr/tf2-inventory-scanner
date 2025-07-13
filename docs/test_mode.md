# Test Mode

The optional `--test` flag saves API responses to `cached_inventories/` so you can work offline.
When you run:

```bash
python run_hypercorn.py --test
```

The server prompts for a SteamID64. It downloads that user's inventory,
player summary and playtime, storing the data under a subdirectory matching the SteamID.
Subsequent runs reuse these files and no network calls are made unless you delete them.
