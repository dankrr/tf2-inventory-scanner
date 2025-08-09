# Functions Reference

## ensure_cache_ready

Ensures required cache files exist before the server starts.

- **Parameters:** none
- **Returns:** `bool` – `True` when the schema is refreshed and a restart is required.
- **Used in:** `run.py`

## main

Bootstraps the application, refreshes cache as needed, configures Hypercorn, and starts serving the Flask app.

- **Parameters:** none
- **Returns:** `None`
- **Used in:** `run.py`
