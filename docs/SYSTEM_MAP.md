# System Map

- **app.py** – Flask application with routes for scanning users and retrying failed scans.
- **templates/index.html** – Displays input form, two result buckets, and a floating refresh button that scrolls to the top before retrying failures.
- **static/submit.js** – Handles form submission, defines `addCardToBucket`, and keeps public cards before private ones in the Completed bucket.
- **static/retry.js** – Manages retry logic, modal interactions, per-user search binding, floating refresh control, and provides an `addCardToBucket` fallback.
- **static/style.css** – Provides styling including bucket layout and jump button.
- **static/ui.js** – Provides global display toggles and extends handler binding.
