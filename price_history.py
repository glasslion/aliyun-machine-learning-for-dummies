# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from tabulate import tabulate

from utils import Config, do_action, RegionIdSelect, ZonesSelect

from aliyunsdkecs.request.v20140526 import DescribeSpotPriceHistoryRequest
from aliyunsdkecs.request.v20140526 import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526 import DescribeZonesRequest



def main():
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')

    client  = config.create_api_client('cn-hongkong')
    RegionIdSelect().show(config, client=client)
    ZonesSelect().show(config)
    client  = config.create_api_client()

    table = []
    request = DescribeSpotPriceHistoryRequest.DescribeSpotPriceHistoryRequest()
    request.set_ZoneId(config.get(['CreateInstanceParams', 'ZoneId']))
    request.set_NetworkType('vpc')
    request.set_InstanceType('ecs.gn5-c4g1.xlarge')
    start_time = datetime.now() - timedelta(days=29)
    request.set_StartTime(start_time.strftime('%Y-%m-%dT00:00:00Z'))
    result = do_action(client, request)
    for item in result['SpotPrices']['SpotPriceType']:
        table.append((item['Timestamp'], item['SpotPrice']))
    print(tabulate(table))


def get_zones(client):
    request = DescribeZonesRequest.DescribeZonesRequest()
    result = do_action(client, request)
    return result['Zones']['Zone']


if __name__ == "__main__":
    main()