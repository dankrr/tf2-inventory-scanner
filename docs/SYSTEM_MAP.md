# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans.
- **templates/index.html** – Displays input form, two result buckets, and floating top/refresh buttons.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, and keeps public cards before private ones in the Completed bucket.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating controls, and provides an `addCardToBucket` fallback.
- **static/style.css** – Provides styling including bucket layout, jump button, and floating controls.
- **static/ui.js** – Provides global display toggles and extends handler binding.
