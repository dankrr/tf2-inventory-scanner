import json
import utils.schema_fetcher as sf


def test_schema_loads_files(tmp_path, monkeypatch):
    defs = {"1": {"name": "One"}}
    quals = {"0": "Normal"}
    dpath = tmp_path / "defindexes.json"
    qpath = tmp_path / "qualities.json"
    dpath.write_text(json.dumps(defs))
    qpath.write_text(json.dumps(quals))
    for key in sf.FILES:
        if key == "defindexes":
            monkeypatch.setitem(sf.FILES, key, dpath)
        elif key == "qualities":
            monkeypatch.setitem(sf.FILES, key, qpath)
        else:
            monkeypatch.setitem(sf.FILES, key, tmp_path / f"{key}.json")
    sf.SCHEMA = None
    sf.QUALITIES = {}
    sf.PROPERTIES = {}
    schema = sf.ensure_schema_cached()
    assert schema == defs
    assert sf.QUALITIES == quals
