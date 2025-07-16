# Startup Flow

This document shows the overall startup sequence of the server and how the cache is validated.

## Cache Validation & Restart Logic

When the application launches it calls `fetch_missing_cache_files()` before starting the web server.

```
ok, refreshed, schema_refreshed = await fetch_missing_cache_files()
```

- If `ok` is `False` the process exits.
- If `schema_refreshed` is `True` the application restarts using `os.execv()` so the in-memory schema is reloaded.
- When only prices or currencies were refreshed the server continues without a restart.

### Sequence

```
Startup -> fetch_missing_cache_files() ->
  [schema_refreshed? yes] -> restart process
  [schema_refreshed? no]  -> continue server startup
```
