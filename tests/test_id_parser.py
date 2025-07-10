import asyncio
import utils.steam_api_client as sac
from utils.id_parser import extract_steam_ids


def test_extract_ids_from_status_block(monkeypatch):
    text = """
    hostname: my tf2 server
    version : 123
    # userid name uniqueid connected ping loss state
    #   314 "Xanmangamer" [U:1:876151635] 00:26 94 74 spawning
    #   315 "Tester" [U:1:1137042230] 01:11 88 0 active
    #   316 "Short" [U:1:2] 00:01 50 0 active
    """

    ids = extract_steam_ids(text)

    assert "Xanmangamer" in ids
    assert "Tester" in ids
    assert "Short" in ids

    mapping = {
        "[U:1:876151635]": "76561198836417363",
        "[U:1:1137042230]": "76561199097307958",
        "[U:1:2]": "76561197960265730",
        "Xanmangamer": "76561198000000001",
        "Tester": "76561198000000002",
        "Short": "76561198000000003",
    }

    async def fake_convert(id_str: str) -> str:
        if id_str in mapping:
            return mapping[id_str]
        raise ValueError(id_str)

    monkeypatch.setattr(sac, "convert_to_steam64", fake_convert)

    steam64 = []
    for i in ids:
        try:
            steam64.append(asyncio.run(sac.convert_to_steam64(i)))
        except ValueError:
            continue

    assert steam64 == [
        mapping["Xanmangamer"],
        mapping["[U:1:876151635]"],
        mapping["Tester"],
        mapping["[U:1:1137042230]"],
        mapping["Short"],
        mapping["[U:1:2]"],
    ]
