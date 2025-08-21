from utils.schema_provider import has_attribute
from utils.inventory.filters_and_rules import _has_attr
from utils.inventory.tools_and_kits import _extract_killstreak_tool_info
from utils.inventory.extract_attr_classes import resolve_attr_defindex


def test_has_attribute_none_defindex():
    assert has_attribute([], None) is False


def test__has_attr_none_defindex():
    assert _has_attr({"attributes": []}, None) is False


def test_extract_killstreak_tool_info_handles_missing():
    asset = {"defindex": 6527, "attributes": []}
    info = _extract_killstreak_tool_info(asset)
    assert info is not None
    assert info["weapon_defindex"] is None


def test_resolve_attr_defindex_missing():
    assert resolve_attr_defindex("nonexistent") is None
