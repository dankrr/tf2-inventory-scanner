# Inventory Enrichment Pipeline

This document describes the structure of enriched inventory items returned by the Flask backend.

## Modal Payload

The item detail modal expects certain fields when rendering an item. Each inventory item embedded in the HTML snippet contains a `data-item` JSON payload with the following keys:

- `custom_name`: user defined name or `null`
- `name`: base item name
- `unusual_effect`: text description of any unusual effect
- `image_url`: URL to the item's icon
- `item_type_name`: type string from the schema
- `level`: numeric level value
- `origin`: source of the item
- `paint_name`: readable paint name if painted
- `paint_hex`: hex color used for the paint dot
- `wear_name`: wear tier for decorated weapons
- `paintkit_name`: warpaint identifier
- `crate_series_name`: crate series label if applicable
- `custom_description`: custom description text
- `strange_parts`: array of strange part names
- `spells`: array of Halloween spell names
- `badges`: array of objects with `icon` and `title`

Any additional field required by the modal should be added to this list and passed through the enrichment pipeline to maintain compatibility.
