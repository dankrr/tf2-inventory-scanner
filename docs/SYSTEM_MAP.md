# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans.
- **templates/index.html** – Displays input form, two result buckets, floating top/refresh buttons, and a settings gear.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, keeps public cards before private ones in the Completed bucket, and uses the shared `scanToast` controller.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating controls, and exposes the global `scanToast` lifecycle helpers (`start`, `tick`, `finish`, `setProgress`) plus legacy wrappers.
- **static/style.css** – Provides styling including bucket layout, jump button, floating controls, the settings menu, and hard-hides legacy header toggles. Loads Font Awesome for icons.
- **static/ui.js** – Provides global display toggles, floating settings menu logic, injects Font Awesome gear, Compact, and Border Mode icons, mirrors legacy icons, and extends handler binding.
