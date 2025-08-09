# Architecture

The TF2 Inventory Scanner is a Flask application that serves a web interface for inspecting player inventories. The application starts through `run.py`, which prepares cache files and runs the app with Hypercorn.

Containerized deployments rely on a single service defined in `docker-compose.yml`. The service builds from the repository's `Dockerfile`, mounts the local `./app` directory to `/app` inside the container, loads environment variables from `.env`, and exposes port `5000`.
