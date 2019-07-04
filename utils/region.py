from aliyunsdkecs.request.v20140526 import (
    DescribeRegionsRequest, DescribeZonesRequest
)

from .select import BaseConfigParameterSelect


class RegionIdSelect(BaseConfigParameterSelect):
    name = "地域"
    key = "RegionId"
    request_cls = DescribeRegionsRequest.DescribeRegionsRequest
    items_getter = lambda self, x: x['Regions']['Region']
    item_key = "RegionId"
    select_item_formatter = lambda self, x: "{}({})".format(x['LocalName'], x['RegionId'])


class ZonesSelect(BaseConfigParameterSelect):
    name = "可用区"
    key = ['CreateInstanceParams', 'ZoneId']
    request_cls = DescribeZonesRequest.DescribeZonesRequest
    items_getter = lambda self, x: x['Zones']['Zone']
    item_key = "ZoneId"
    select_item_formatter = lambda self, x: "{} {}".format(x['ZoneId'], x['LocalName'])
