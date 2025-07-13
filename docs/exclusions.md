# Exclusions File

The application loads a small JSON configuration to hide item origins and tweak craft weapon detection.

## Location

The file lives at `static/exclusions.json` and is parsed by `utils.local_data.load_exclusions()` when the server starts.

## Format

```json
{
  "hidden_origins": [0, 1, 5, 14],
  "craft_weapon_exclusions": [1, 5, 9, 14]
}
```

- **hidden_origins** – origins in this list are ignored completely.
- **craft_weapon_exclusions** – items from these origins will not be flagged as plain craft weapons.

## Modifying Rules

1. Open `static/exclusions.json` in your editor.
2. Add origin IDs to a list to enable the rule.
3. Remove IDs from a list to disable the rule.
4. Save the file and restart the app for changes to take effect.
