# Testing Guide

This guide explains how to run the test suite and describes the cache refresh tests.

## Running Tests

Use `pytest` to execute all tests:

```bash
pytest -q
```

During local development you can skip cache validation by setting `SKIP_CACHE_INIT=1` to speed up startup.

## Cache Manager Tests

`tests/test_cache_manager.py` contains tests for the selective cache refresh logic:

- **`test_schema_only_refresh`** – ensures schema refresh triggers a restart.
- **`test_pricing_only_refresh`** – prices refresh without requiring restart.
- **`test_mixed_refresh`** – both schema and prices are refreshed; restart required.

Each test uses monkeypatching to simulate network operations.
