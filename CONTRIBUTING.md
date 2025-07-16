# Contributing

Run `pre-commit` and the legacy cache check before pushing changes.

```bash
pre-commit run --files <files>
python scripts/check_legacy.py
```

CI pipelines should execute `python scripts/check_legacy.py` and fail if any old cache files remain.
