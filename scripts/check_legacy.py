#!/usr/bin/env python3
"""Fail CI if legacy cache files exist."""
from pathlib import Path

LEGACY_PATHS = [Path("cache/string_lookups.json")]


def main() -> int:
    found = [p for p in LEGACY_PATHS if p.exists()]
    if found:
        print("Legacy cache files detected:")
        for p in found:
            print(f"- {p}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
