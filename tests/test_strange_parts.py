import struct
from utils import inventory_processor as ip
from utils import local_data as ld


def test_part_name_and_score_types(monkeypatch):
    mapping = {
        23: "Gib Kills",
        95: "Assists",
        80: "Killstreaks Ended",
    }
    monkeypatch.setattr(ld, "KILL_EATER_TYPES", mapping, False)

    val = struct.unpack("<I", struct.pack("<f", 23.0))[0]
    asset = {"attributes": [{"defindex": 380, "value": val, "float_value": 23.0}]}

    counts, types = ip._extract_kill_eater_info(asset)
    assert counts == {}
    assert types == {2: 23}
    assert ip._part_name(23) == "Gib Kills"
    assert ip._part_name(95) == "Assists"
    assert ip._part_name(80) == "Killstreaks Ended"
