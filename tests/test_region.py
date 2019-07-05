from utils.region import RegionIdSelect, ZonesSelect
from .fixture import config


def test_RegionIdSelect(config):
    sel =  RegionIdSelect(config)
    items = sel.get_items()

    regions = [item[sel.item_key] for item in items]
    assert 'cn-hangzhou' in regions
    assert 'cn-shanghai' in regions


def test_ZonesSelect(config):
    config.set("RegionId", 'cn-shanghai')
    sel =  ZonesSelect(config)
    items = sel.get_items()

    zones = [item[sel.item_key] for item in items]
    assert 'cn-shanghai-b' in zones
