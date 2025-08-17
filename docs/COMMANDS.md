# Commands

| Command                                                                                                                                                                                                                                 | Description                       |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| `npx eslint static/submit.js static/retry.js static/ui.js`                                                                                                                                                                              | Lint JavaScript files.            |
| `npx prettier -w templates/index.html static/submit.js static/retry.js static/style.css static/ui.js docs/ARCHITECTURE.md docs/FUNCTIONS_REFERENCE.md docs/COMMANDS.md docs/SYSTEM_MAP.md docs/DEVELOPERS_GUIDE.md CHANGELOG.md`        | Format modified files.            |
| `pre-commit run --files templates/index.html static/submit.js static/retry.js static/style.css static/ui.js docs/ARCHITECTURE.md docs/FUNCTIONS_REFERENCE.md docs/COMMANDS.md docs/SYSTEM_MAP.md docs/DEVELOPERS_GUIDE.md CHANGELOG.md` | Run repository linters and tests. |
