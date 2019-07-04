# -*- coding: utf-8 -*-
import concurrent.futures

from tabulate import tabulate

import click

from utils import Config, do_action

from aliyunsdkecs.request.v20140526 import DescribeSpotPriceHistoryRequest
from aliyunsdkecs.request.v20140526 import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526 import DescribeZonesRequest


def query_price(config, region, zone, instance_type):
    client  = config.create_api_client(region['RegionId'])
    request = DescribeSpotPriceHistoryRequest.DescribeSpotPriceHistoryRequest()
    request.set_ZoneId(zone['ZoneId'])
    request.set_NetworkType('vpc')
    request.set_InstanceType(instance_type)
    result = do_action(client, request)
    ret = []
    try:
        item = result['SpotPrices']['SpotPriceType'][-1]
        ret.append(
            [
                zone['LocalName'],
                instance_type,
                item['Timestamp'],
                item['SpotPrice']
            ]
        )
    except IndexError:
        pass
    return ret


@click.command()
@click.option(
    '--max-price', '-m', type=float, default=1000,
    help="max price (per hour)")
@click.option(
    '--type', '-t', default='gn', help="Instance type",
    type=str)
    # type=click.Choice(['gn', 'r5', 'se1', 'g5', 'i2']))
def main(max_price, type):
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')

    click.echo("由于需要对地域，可用区， 实例类型的每种组合都查询一次价格， 查询时间可能较长， 请耐心等待")

    client  = config.create_api_client('cn-hongkong')
    regions = get_regions(client)
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        for region in regions:
            client  = config.create_api_client(region['RegionId'])
            zones = get_zones(client)
            for zone in zones:
                ins_types = zones[0]['AvailableInstanceTypes']['InstanceTypes']
                ins_types = [t for t in ins_types if t.startswith('ecs.{}'.format(type))]
                if 'ecs.gn5-c4g1.xlarge' not in ins_types:
                    # 由于阿里云方面的bug, DescribeZonesRequest 返回的 AvailableInstanceTypes 可能不全
                    # 这里手动插入些最常用的实例类型
                    ins_types.append('ecs.gn5-c4g1.xlarge')
                for instance_type in ins_types:
                    # query_price(config, region, zone, instance_type)
                    future = executor.submit(
                        query_price,
                        config, region, zone, instance_type,
                    )

                    futures.append(future)
    table = []
    for future in concurrent.futures.as_completed(futures):
        try:
            data = future.result()
            table.extend(data)
        except Exception as exc:
            print('Generated an exception: %s' % (exc))

    table  = [row for row in table if row[-1]< max_price]
    table.sort(key=lambda x: (x[0], x[-1]))
    print(tabulate(table))


def get_regions(client):
    request = DescribeRegionsRequest.DescribeRegionsRequest()
    result = do_action(client, request)
    return result['Regions']['Region']

def get_zones(client):
    request = DescribeZonesRequest.DescribeZonesRequest()
    result = do_action(client, request)
    return result['Zones']['Zone']


if __name__ == "__main__":
    main()
