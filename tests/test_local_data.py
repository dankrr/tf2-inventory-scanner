import importlib
import json
from types import ModuleType

import os
from utils import local_data as ld


def reload_with(tmp_path, schema=None, ig=None) -> ModuleType:
    if schema is None:
        schema = {"items": {"1": {"name": "One"}}, "qualities": {"Normal": 0}}
    if ig is None:
        ig = {"paints": {"1": {"name": "Red", "hex": "#f00"}}}
    schema_file = tmp_path / "tf2_schema.json"
    items_file = tmp_path / "items_game_cleaned.json"
    schema_file.write_text(json.dumps(schema))
    items_file.write_text(json.dumps(ig))
    os.environ["TF2_SCHEMA_FILE"] = str(schema_file)
    os.environ["TF2_ITEMS_GAME_FILE"] = str(items_file)
    importlib.invalidate_caches()
    return importlib.reload(ld)


def test_tables_load_from_cache(tmp_path):
    mod = reload_with(tmp_path)
    assert mod.TF2_SCHEMA["1"]["name"] == "One"
    assert mod.PAINTS[1]["hex"] == "#f00"
