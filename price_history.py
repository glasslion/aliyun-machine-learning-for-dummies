# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from tabulate import tabulate

from utils import Config, do_action, RegionIdSelect, ZonesSelect

import click

from aliyunsdkecs.request.v20140526 import DescribeSpotPriceHistoryRequest
from aliyunsdkecs.request.v20140526 import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526 import DescribeZonesRequest


@click.command()
@click.option('--merge', default=True)
def main(merge):
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
    instance_type = click.prompt('请输入你要查询的实例规格', type=str, default='ecs.gn5-c4g1.xlarge')
    request.set_InstanceType(instance_type)
    start_time = datetime.now() - timedelta(days=29)
    request.set_StartTime(start_time.strftime('%Y-%m-%dT00:00:00Z'))
    result = do_action(client, request)
    for idx, item in enumerate(result['SpotPrices']['SpotPriceType']):
        if merge and idx > 0:
            prev_item = result['SpotPrices']['SpotPriceType'][idx-1]
            if item['SpotPrice'] != prev_item['SpotPrice']:
                table.append((item['Timestamp'], item['SpotPrice']))
        else:
            table.append((item['Timestamp'], item['SpotPrice']))
    if not table:
        print('找不到该区域实例的历史价格记录')
    print(tabulate(table))


def get_zones(client):
    request = DescribeZonesRequest.DescribeZonesRequest()
    result = do_action(client, request)
    return result['Zones']['Zone']


if __name__ == "__main__":
    main()