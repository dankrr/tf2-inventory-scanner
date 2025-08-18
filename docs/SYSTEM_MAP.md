# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans.
- **templates/index.html** – Displays input form, two result buckets, floating top/refresh buttons, and a settings gear.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, and keeps public cards before private ones in the Completed bucket.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating controls, provides an `addCardToBucket` fallback, and shows Steam API health hints via toast notifications after repeated refresh failures.
- **static/style.css** – Provides styling including bucket layout, jump button, floating controls, the settings menu, toast notifications, and hard-hides legacy header toggles. Loads Font Awesome for icons.
- **static/ui.js** – Provides global display toggles, floating settings menu logic, injects Font Awesome gear, Compact, and Border Mode icons, mirrors legacy icons, and extends handler binding.
