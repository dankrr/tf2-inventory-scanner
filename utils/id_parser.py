"""Deprecated wrappers for Steam ID parsing.

Use :mod:`utils.steam_api_client` for the canonical implementations.
"""

from .steam_api_client import convert_to_steam64, extract_steam_ids

__all__ = ["convert_to_steam64", "extract_steam_ids"]
