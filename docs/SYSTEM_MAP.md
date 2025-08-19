# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans; normalizes missing payloads into failed stubs with error metadata.
- **templates/index.html** – Displays input form, two result buckets, floating top/refresh buttons, and a settings gear.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, and keeps public cards before private ones in the Completed bucket.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating controls, and provides an `addCardToBucket` fallback.
- **static/style.css** – Provides styling including bucket layout, jump button, floating controls, the settings menu, and hard-hides legacy header toggles. Loads Font Awesome for icons. Adds gradient quality rings and 45° accents for dual-quality items in Border Mode.
- **static/ui.js** – Provides global display toggles, floating settings menu logic, injects Font Awesome gear, Compact, and Border Mode icons, mirrors legacy icons, and extends handler binding. Computes quality palette colors and split-ring styles.
