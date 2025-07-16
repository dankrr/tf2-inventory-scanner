import asyncio
import os
import sys

from hypercorn.asyncio import serve
from hypercorn.config import Config

from app import app, kill_process_on_port, _setup_test_mode, ARGS
from utils.cache_manager import fetch_missing_cache_files


async def ensure_cache_ready() -> None:
    """Ensure cache files exist before starting the server."""
    ok, _, _ = await fetch_missing_cache_files()
    if not ok:
        sys.exit(1)


async def main() -> None:
    await ensure_cache_ready()
    port = int(os.getenv("PORT", 5000))
    kill_process_on_port(port)
    if ARGS.test:
        await _setup_test_mode()
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.use_reloader = not ARGS.test
    await serve(app, config)


if __name__ == "__main__":
    asyncio.run(main())
