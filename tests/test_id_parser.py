# ruff: noqa: E402
import os

os.environ.setdefault("BACKPACK_API_KEY", "x")

import utils.steam_api_client as sac
from utils.id_parser import extract_steam_ids


def test_extract_ids_from_status_block():
    text = """
    hostname: my tf2 server
    version : 123
    # userid name uniqueid connected ping loss state
    #   314 "Xanmangamer" [U:1:876151635] 00:26 94 74 spawning
    #   315 "Tester" [U:1:1137042230] 01:11 88 0 active
    #   316 "Short" [U:1:2] 00:01 50 0 active
    """
    ids = extract_steam_ids(text)
    steam64 = [sac.convert_to_steam64(i) for i in ids]
    assert steam64 == [
        sac.convert_to_steam64("[U:1:876151635]"),
        sac.convert_to_steam64("[U:1:1137042230]"),
        sac.convert_to_steam64("[U:1:2]"),
    ]
    assert "Xanmangamer" not in ids
    assert "active" not in ids
