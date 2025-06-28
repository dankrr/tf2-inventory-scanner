"""Utilities for building a decorated weapon name mapping."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import vdf

WEAR_TIERS = {
    1: "Battle-Scarred",
    2: "Well-Worn",
    3: "Field-Tested",
    4: "Minimal Wear",
    5: "Factory New",
}


def load_items_game(path: str | Path) -> Dict[str, Any]:
    """Load items_game data from JSON or VDF file."""
    p = Path(path)
    text = p.read_text()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = vdf.loads(text)
    return data.get("items_game", data)


def generate_warpaint_mapping(items_game: Dict[str, Any]) -> Dict[str, str]:
    """Return mapping of decorated weapons to display names."""
    items = items_game.get("items", {})
    paintkits = items_game.get("paintkits", {})
    kit_names = {
        str(k): v.get("name") or v.get("description_string", str(k))
        for k, v in paintkits.items()
    }

    mapping: Dict[str, str] = {}
    for defindex, item in items.items():
        paintkit = item.get("paintkit")
        if not paintkit:
            continue
        base_name = item.get("item_name") or item.get("name") or f"Item #{defindex}"
        kit_name = kit_names.get(str(paintkit), str(paintkit))
        for wear_id, wear_name in WEAR_TIERS.items():
            key = f"{defindex};decorated;{wear_id}"
            display = f"War-painted {base_name} ({kit_name}) ({wear_name})"
            mapping[key] = display
    return mapping


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate warpaint mapping")
    parser.add_argument("items_game", type=Path)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("utils/warpaint_mapping.json"),
    )
    args = parser.parse_args(argv)

    data = load_items_game(args.items_game)
    mapping = generate_warpaint_mapping(data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w") as f:
        json.dump(mapping, f, indent=2, sort_keys=True)
    print(f"Wrote {len(mapping)} entries to {args.output}")


if __name__ == "__main__":
    main()
