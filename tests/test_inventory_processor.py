import json
from utils.inventory_processor import process_inventory, PLACEHOLDER_IMG


def test_process_inventory_names_and_placeholder(tmp_path):
    with open('tests/sample_inventory.json') as f:
        data = json.load(f)
    items = data['result']['items']
    processed = process_inventory(items)
    assert processed[0]['name'] == 'Vintage Merryweather'
    assert processed[1]['name'] == 'Ghastlierest Gibus'
    assert processed[1]['image_url'] == PLACEHOLDER_IMG
