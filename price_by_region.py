# -*- coding: utf-8 -*-
from tabulate import tabulate

from utils import Config, do_action

from aliyunsdkecs.request.v20140526 import DescribeSpotPriceHistoryRequest
from aliyunsdkecs.request.v20140526 import DescribeRegionsRequest
from aliyunsdkecs.request.v20140526 import DescribeZonesRequest



def main():
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')
    client  = config.create_api_client('cn-hongkong')

    table = []
    client = config.create_api_client()
    regions = get_regions(client)
    for region in regions:
        client  = config.create_api_client(region['RegionId'])
        zones = get_zones(client)
        for zone in zones:
            ins_types = zones[0]['AvailableInstanceTypes']['InstanceTypes']
            ins_types = [t for t in ins_types if t.startswith('ecs.gn')]
            if 'ecs.gn5-c4g1.xlarge' not in ins_types:
                # 由于阿里云方面的bug, DescribeZonesRequest 返回的 AvailableInstanceTypes 可能不全
                # 这里手动插入些最常用的实例类型
                ins_types.append('ecs.gn5-c4g1.xlarge')
            for instance_type in ins_types:
                request = DescribeSpotPriceHistoryRequest.DescribeSpotPriceHistoryRequest()
                request.set_ZoneId(zone['ZoneId'])
                request.set_NetworkType('vpc')

                request.set_InstanceType(instance_type)
                result = do_action(client, request)
                try:
                    item = result['SpotPrices']['SpotPriceType'][-1]
                    table.append([zone['LocalName'], instance_type, item['Timestamp'], item['SpotPrice']])
                except IndexError:
                    pass
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