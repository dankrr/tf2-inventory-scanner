from utils.helpers import best_match_from_keys


def test_best_match_success():
    keys = ["Warhawk", "Airwolf", "Carpet Bomber"]
    assert best_match_from_keys("Carpet Bomb", keys) == "Carpet Bomber"


def test_best_match_none():
    keys = ["Warhawk", "Airwolf"]
    assert best_match_from_keys("Totally Different", keys) is None
