from utils.id_parser import extract_steam_ids


def test_extract_ids_from_mixed_input():
    text = """
    #    354 "AnonyMouse"        [U:1:1110742403]
    76561198881990960
    STEAM_0:0:88939219
    somename
    [U:1:99950348]
    anotherusername
    """
    ids = extract_steam_ids(text)
    assert ids == [
        "76561199071008131",
        "76561198881990960",
        "76561198138144166",
        "76561198060216076",
    ]


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
    assert ids == [
        "76561198836417363",
        "76561199097307958",
        "76561197960265730",
    ]


def test_extract_ids_with_embedded_tokens():
    text = (
        "Yyffjjuggv [U:1:86514219]. Bbbkiiyccc "
        '# 2 "Player" STEAM_0:0:12345678 00:03 50 0 active'
    )
    ids = extract_steam_ids(text)
    assert ids == [
        "76561198046779947",
        "76561197984957084",
    ]
