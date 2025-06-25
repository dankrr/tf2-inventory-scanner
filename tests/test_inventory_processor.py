import json
from utils.inventory_processor import process_inventory


def test_process_inventory_limits_and_images(tmp_path):
    with open('tests/sample_inventory.json') as f:
        data = json.load(f)
    items = data['result']['items'] * 30
    processed = process_inventory(items)
    assert processed[0]['name'] == 'Vintage Merryweather'
    assert processed[1]['name'] == 'Ghastlierest Gibus'
    assert processed[0]['image_url'].startswith('https://')
    assert len(processed) == 50
