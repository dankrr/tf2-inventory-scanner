# Refreshing Data

Item schema data is saved to `data/schema_steam.json` while price files live
under `cache/`. The schema is refreshed automatically if the file is older than
24 hours whenever the server starts. Use the `--refresh` flag to force a manual
download before running the server.

```bash
python app.py --refresh --verbose
```

The command downloads the latest schema file to `data/schema_steam.json` and
updates backpack.tf prices and currency data in the `cache/` directory. After it
completes, start the server normally:

```bash
python run_hypercorn.py
```

Run the refresh step whenever you want to update your local data.
