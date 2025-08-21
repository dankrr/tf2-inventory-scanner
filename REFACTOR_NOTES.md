# Refactor Notes

- Split `utils/inventory_processor.py` into a dedicated `utils/inventory/` package.
- Moved attribute class caching to `extract_attr_classes.py`.
- Extracted constant maps to `maps_and_constants.py`.
- Separated extraction helpers into focused modules for unusual effects, paint/wear,
  miscellaneous fields, warpaint tools, naming, and rule filters.
- Added `processor.py` hosting `_process_item` and `api.py` for public wrappers.
- The original `inventory_processor.py` now re-exports the API functions for
  backward compatibility.
