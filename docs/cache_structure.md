# Cache Structure

All schema files are stored under `cache/schema/`. When new versions are downloaded, outdated files from older paths are removed automatically.

Legacy files such as `cache/string_lookups.json` are deleted when `utils.local_data.cleanup_legacy_files()` runs. You can also enforce this in CI with `scripts/check_legacy.py`.

```bash
python scripts/check_legacy.py
```
