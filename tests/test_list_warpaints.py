import json
import importlib

import scripts.list_warpaints as lw


def test_list_warpaints(tmp_path, capsys, monkeypatch):
    base = tmp_path
    schema = base / "cache" / "schema"
    schema.mkdir(parents=True)
    (schema / "warpaints.json").write_text(json.dumps({"Test Paint": 1}))
    (schema / "items.json").write_text(
        json.dumps([{"defindex": 42, "item_name": "Pistol"}])
    )
    inv_dir = base / "cached_inventories"
    inv_dir.mkdir()
    (inv_dir / "inv.json").write_text(
        json.dumps(
            {
                "items": [
                    {
                        "defindex": 42,
                        "attributes": [{"defindex": 834, "float_value": 1}],
                    }
                ]
            }
        )
    )

    importlib.reload(lw)
    monkeypatch.setattr(lw, "BASE_DIR", base)
    lw.main()
    out = capsys.readouterr().out.strip()
    assert out == "Test Paint Pistol"
