import asyncio
import os

from hypercorn.asyncio import serve
from hypercorn.config import Config

from app import app, kill_process_on_port, _setup_test_mode, ARGS


async def main() -> None:
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
