# Refreshing Data

Item schema and price information is cached under `cache/` so the application can
start quickly and work offline. These files can get stale over time. Use the
`--refresh` flag to download the latest versions before running the server.

```bash
python app.py --refresh --verbose
```

The command downloads all TF2 schema files, backpack.tf prices and currency data
into the `cache/` directory. After it completes, start the server normally:

```bash
python run_hypercorn.py
```

Run the refresh step whenever you want to update your local data.
