#!/usr/bin/env python
"""Check that required attributes exist in the local schema."""

from __future__ import annotations

import os

from utils import local_data

# attribute defindex -> human readable name
REQUIRED_ATTRS = {
    134: "Unusual Effect",
    2041: "Unusual Effect (new)",
    142: "Paint Color",
    261: "Paint Color (legacy)",
    725: "Wear",
    834: "Paintkit",
    2025: "Killstreak Tier",
    2014: "Killstreak Sheen",
    2013: "Killstreaker",
    2027: "Australium Item",
    187: "Crate Series",
    866: "Paintkit Seed Lo",
    867: "Paintkit Seed Hi",
    # Spells
    **{idx: "Spell" for idx in range(8900, 8926)},
}


def main() -> int:
    """Load schema and print status for each required attribute."""
    if os.getenv("SKIP_VALIDATE"):
        print("Schema validation skipped.")
        return 0
    try:
        attributes, _ = local_data.load_files()
    except Exception as exc:  # pragma: no cover - filesystem issues
        print(f"\N{CROSS MARK} Failed to load schema: {exc}")
        return 0 if os.getenv("SKIP_VALIDATE") else 1
    if not attributes:
        print("Schema not found; skipping validation.")
        return 0

    all_ok = True
    for attr_id, label in REQUIRED_ATTRS.items():
        if attr_id in attributes:
            print(f"\N{CHECK MARK} {attr_id} {label}")
        else:
            print(f"\N{CROSS MARK} {attr_id} {label}")
            all_ok = False
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
