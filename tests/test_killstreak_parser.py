import utils.killstreak_parser as kp


def test_parse_killstreak_kit():
    asset = {
        "id": 1,
        "defindex": 6526,
        "attributes": [
            {"defindex": 2012, "float_value": 36},
            {"defindex": 2014, "float_value": 5},
            {"defindex": 2013, "float_value": 2006},
        ],
    }
    names = {"36": "Blutsauger"}
    parsed = kp.parse_killstreak_item(asset, defindex_names=names)
    assert parsed["tier"] == "Professional Killstreak Kit"
    assert parsed["weapon_name"] == "Blutsauger"
    assert parsed["sheen"] == "Agonizing Emerald"
    assert parsed["killstreaker"] == "Singularity"


def test_parse_killstreak_fabricator():
    asset = {
        "id": 2,
        "defindex": 20003,
        "attributes": [
            {
                "defindex": 2006,
                "is_output": True,
                "itemdef": 6523,
                "attributes": [
                    {"defindex": 2014, "float_value": 2},
                    {"defindex": 2013, "float_value": 2005},
                    {"defindex": 2012, "float_value": 203},
                ],
            },
            {"defindex": 5706, "itemdef": 5706, "quantity": 19},
            {"defindex": 5707, "itemdef": 5707, "quantity": 5},
        ],
    }
    names = {
        "203": "Unarmed Combat",
        "5706": "Battle-Worn Robot KB-808",
        "5707": "Battle-Worn Robot Taunt Processor",
    }
    parsed = kp.parse_killstreak_item(asset, defindex_names=names)
    assert parsed["tier"] == "Specialized Killstreak Kit"
    assert parsed["weapon_name"] == "Unarmed Combat"
    assert parsed["sheen"] == "Deadly Daffodil"
    assert parsed["killstreaker"] == "Flames"
    assert {"part": "Battle-Worn Robot KB-808", "qty": 19} in parsed["requirements"]
    assert {"part": "Battle-Worn Robot Taunt Processor", "qty": 5} in parsed[
        "requirements"
    ]
