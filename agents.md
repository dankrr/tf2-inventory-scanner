# 🤖 Agent Instructions: TF2 Inventory Scanner

Welcome, AI assistant. You are now contributing to the `tf2-inventory-scanner` project — a Flask web app that scans and displays Team Fortress 2 inventories based on Steam IDs.

## 🧠 Project Purpose

- Accept user-submitted Steam IDs in any format (SteamID64, SteamID2/3, vanity).
- Resolve valid IDs, fetch TF2 inventories, and show them visually.
- Use the Steam Web API first; fall back to steamwebapi.com if needed.
- Display:
  - Avatar
  - Playtime (TF2 hours)
  - Item names and images
  - Quality styling (border or background)
  - Links to Steam and backpack.tf profiles

---

## 🔧 Areas to Improve or Extend

### 1. 🧱 UI / UX Improvements

- [ ] Convert `index.html` to Bootstrap 5 layout (cards, responsive grid).
- [ ] Add loading spinner when inventory scan is running.
- [ ] Replace inline quality backgrounds with **quality-colored borders**.
- [ ] Use better font hierarchy and spacing between sections.
- [ ] Ensure mobile friendliness (cards wrap properly on small screens).

---

### 2. 🧠 ID Input and Resolution

- [ ] Support resolving:
  - SteamID2 (e.g., `STEAM_0:1:123456`)
  - SteamID3 (e.g., `[U:1:246913]`)
  - Vanity URLs → SteamID64
- [ ] Filter out lines that are not Steam ID formats.
- [ ] Strip duplicates and whitespace before processing.
- [ ] Ensure batch size of up to 20 SteamIDs per submission is handled gracefully.

---

### 3. ⚙️ Backend Enhancements

- [ ] Add helper in `inventory_processor.py` to map defindex → human-readable name.
- [ ] Optionally load item schema from Backpack.tf or Steam schema API and cache it locally.
- [ ] Show "Private Inventory" badge or error on API 403/400 responses.
- [ ] If `icon_url` is missing for any item, use a placeholder image.
- [ ] Optimize performance by batching profile lookups if possible.

---

### 4. 💰 Optional Feature: Item Valuation

- [ ] Add price lookup using Backpack.tf IGetPrices API (use `.env` key if needed).
- [ ] Display item value next to name, e.g., "Strange Rocket Launcher (5.33 ref)"
- [ ] Sort items by value descending inside inventory blocks.

---

### 5. 🌍 Deployment Enhancements

- [ ] Add `Procfile` for Heroku.
- [ ] Add `Dockerfile` for containerized deployment.
- [ ] Add optional `render.yaml` or `fly.toml` for Render/Fly.io deployment.
- [ ] Add `.gitignore` with `/__pycache__/`, `/.venv/`, `.env`

---

## 🧪 Bonus

- [ ] Add tests for SteamID conversion logic
- [ ] Create a test JSON of a sample inventory to test UI layout without live API
- [ ] Log timeouts and API failures clearly in the console

---

## 🛠️ Notes for Codex/Copilot

- You may create new helper files in `utils/` if needed.
- Don't expose any keys or tokens in code — keep `.env` usage intact.
- All user-facing text should be editable via the template (`index.html`).
- Be cautious with rate limits on Steam API (1 req/sec, mostly).
- Ask before integrating heavy third-party JS or front-end frameworks.

---

## 📍 Commands

```bash
# Local run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py

