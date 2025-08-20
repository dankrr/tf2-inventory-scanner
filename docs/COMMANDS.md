# Commands

| Command                                                                                                                                                                              | Description                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------- |
| `npx eslint .`                                                                                                                                                                       | Lint all JavaScript files.        |
| `npx prettier -w static/submit.js static/retry.js CHANGELOG.md docs/ARCHITECTURE.md docs/FUNCTIONS_REFERENCE.md docs/COMMANDS.md docs/SYSTEM_MAP.md docs/DEVELOPERS_GUIDE.md`        | Format modified files.            |
| `pre-commit run --files static/submit.js static/retry.js CHANGELOG.md docs/ARCHITECTURE.md docs/FUNCTIONS_REFERENCE.md docs/COMMANDS.md docs/SYSTEM_MAP.md docs/DEVELOPERS_GUIDE.md` | Run repository linters and tests. |
