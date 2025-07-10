import utils.steam_api_client as sac
from utils.id_parser import extract_steam_ids


def test_extract_ids_only_valid_formats():
    text = """
    76561198083937853
    STEAM_0:1:61836062
    [U:1:123672125]
    Dankr
    """
    ids = extract_steam_ids(text)
    assert ids == [
        "76561198083937853",
        "STEAM_0:1:61836062",
        "[U:1:123672125]",
    ]
    steam64 = [sac.convert_to_steam64(i) for i in ids]
    assert steam64 == [
        sac.convert_to_steam64("76561198083937853"),
        sac.convert_to_steam64("STEAM_0:1:61836062"),
        sac.convert_to_steam64("[U:1:123672125]"),
    ]
