from utils.warpaint_mapping import generate_warpaint_mapping


def test_generate_warpaint_mapping():
    data = {
        "items": {"15013": {"item_name": "Scattergun", "paintkit": "1"}},
        "paintkits": {"1": {"name": "Macabre Web"}},
    }
    mapping = generate_warpaint_mapping(data)
    assert (
        mapping["15013;decorated;5"]
        == "War-painted Scattergun (Macabre Web) (Factory New)"
    )
    assert len(mapping) == 5
