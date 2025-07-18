import asyncio
import os
import sys

from hypercorn.asyncio import serve
from hypercorn.config import Config

from app import socketio, kill_process_on_port, _setup_test_mode, ARGS
from utils.cache_manager import (
    fetch_missing_cache_files,
    COLOR_YELLOW,
    COLOR_RESET,
)


async def ensure_cache_ready() -> bool:
    """Ensure cache files exist before starting the server.

    Returns ``True`` if the schema was refreshed and a restart is needed.
    """
    ok, _, schema_refreshed = await fetch_missing_cache_files()
    if not ok:
        sys.exit(1)
    return schema_refreshed


async def main() -> None:
    schema_refreshed = await ensure_cache_ready()
    if schema_refreshed and not ARGS.test:
        print(
            f"{COLOR_YELLOW}🔄 Restarting to load updated schema...{COLOR_RESET}",
            flush=True,
        )
        os.execv(sys.executable, [sys.executable] + sys.argv)
    port = int(os.getenv("PORT", 5000))
    kill_process_on_port(port)
    if ARGS.test:
        await _setup_test_mode()
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.use_reloader = not ARGS.test
    await serve(socketio.server, config)


if __name__ == "__main__":
    asyncio.run(main())
