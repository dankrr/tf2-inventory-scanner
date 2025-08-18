# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans.
- **templates/index.html** – Displays input form, two result buckets, and floating top/refresh buttons.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, and keeps public cards before private ones in the Completed bucket.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating controls, and provides an `addCardToBucket` fallback. Adds backdrop and placement helpers for the item modal.
- **static/style.css** – Provides styling including bucket layout, jump button, floating controls, and modal positioning with a blur backdrop.
- **static/ui.js** – Provides global display toggles and extends handler binding.
- **static/modal.js** – Manages item modal rendering and interactions.
