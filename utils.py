# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import os
from collections import OrderedDict
import time

import click
import six
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import (DescribeDisksRequest,
                                            CreateDiskRequest,
                                            DescribeImagesRequest,
                                            DescribeInstancesRequest,
                                            DescribeInstanceTypesRequest,
                                            DescribeKeyPairsRequest,
                                            DescribeRegionsRequest,
                                            DescribeSnapshotsRequest,
                                            DescribeZonesRequest,
                                            DescribeSecurityGroupsRequest)

CONFIG_FILE = 'config.json'

def force_text(s, encoding='utf-8'):
    if isinstance(s, six.binary_type):
        return s.decode(encoding)
    return s

class Config(object):
    def __init__(self, *args, **kwargs):
        self._config = OrderedDict()
        self._secrets  = {}

    def load(self):
        """
        Load configs from the config json file
        """
        try:
            with io.open(CONFIG_FILE, encoding='utf-8') as f:
                self._config = json.loads(f.read(), object_pairs_hook=OrderedDict)
        except (IOError, OSError, ValueError):
            pass

    def save(self):
        """
        Save configs into the config json file
        """
        with io.open(CONFIG_FILE, mode='w', encoding='utf-8') as f:
            return f.write(force_text(json.dumps(self._config, indent=4)))

    def obtain_secret(self, name):
        """
        Obtain a secret config, and store it in self._secrets.
        Lookup the environment variables, if not found, then prompt to the user.
        """
        env_name = 'ALIYUN_{}'.format(name.upper())
        human_name = name.upper().replace('_', ' ')

        if os.environ.get(env_name):
            self._secrets[name] = os.environ.get(env_name).strip(' \r\t\n')
        else:
            self._secrets[name] = click.prompt(
                'Please enter your {}'.format(human_name), type=str, hide_input=True)

    def set(self, key, value):
        """
        Set a key/value config. If the key is a string, it acts like a dict.
        If the given key is a list or tuple, it will set the key hierarchically.
        """
        if isinstance(key, (list, tuple)):
            node = self._config
            for k in key[:-1]:
                node = node.setdefault(k, OrderedDict())
            node[key[-1]] = value
        else:
            self._config[key] = value

    def get(self, key):
        if isinstance(key, (list, tuple)):
            node = self._config
            for k in key:
                node = node.get(k, {})
            return node
        else:
            return self._config.get(key)

    def pop(self, key, default=None):
        if isinstance(key, (list, tuple)):
            node = self._config
            for k in key[:-1]:
                node = node.get(k)
            return node.pop(k, default)
        else:
            return self._config.pop(key, default)

    def config_via_prompt(self):
        """
        Get ecs configs via commandline prompts
        """
        self.load()

        # We need a default region id to initialize the api client,
        # then query other available regions
        default_region_id = 'cn-hangzhou'

        client = client = AcsClient(
            self._secrets['access_key_id'],
            self._secrets['access_key_secret'],
            default_region_id,
        )
        RegionIdSelect().show(config=self, client=client)
        InstanceTypeSelect().show(config=self)
        SecurityGroupsSelect().show(config=self)
        msg = "ECS实例自带的磁盘， 在实例被删除后， 也会被删除。为了保存你的工作， 你需要额外再挂载一块磁盘。\
你可以选择是创建一块全新的磁盘(n)， 还是重用现有的一块磁盘(e)，或者是使用快照创建一块新的磁盘(s), [n/e/s]"
        answer = click.prompt(msg).lower()
        if answer == 'n':
            create_empty_disk(config)
        elif answer == 'e':
            DisksSelect().show(config=self)
        else:
            ZonesSelect().show(config=self)
            SnapshotsSelect().show(config=self)
            create_disk_from_snapshot(config)
        KeyPairsSelect().show(config=self)
        ImagesSelect().show(config=self)

        InstanceName = click.prompt('请输入你的实例名称（便于标识实例）:', default='ecs-ml-01', type=str)
        self.set(['CreateInstanceParams','InstanceName'], InstanceName)

        InternetChargeType = click.prompt(
            '请设置网络计费类型(PayByBandwidth|PayByTraffic): ',
            default='PayByTraffic', type=str)
        self.set(['CreateInstanceParams','InternetChargeType'], InternetChargeType)

        InternetMaxBandwidthOut = click.prompt('请设置公网出口带宽(单位 MB), 必须大于0， 否则无法分配公网 IP', type=int, default=25)
        self.set(['CreateInstanceParams','InternetMaxBandwidthOut'], InternetMaxBandwidthOut)

        SpotStrategy = click.prompt(
            '请设置后付费实例的竞价策略(NoSpot|SpotWithPriceLimit|SpotAsPriceGo):',
            default='SpotWithPriceLimit', type=str)
        self.set(['CreateInstanceParams','SpotStrategy'], SpotStrategy)

        SpotPriceLimit = click.prompt('请设置实例的每小时最高价格', type=float)
        self.set(['CreateInstanceParams','SpotPriceLimit'], SpotPriceLimit)

        self.save()

    def create_api_client(self):
        return AcsClient(
            self._secrets['access_key_id'],
            self._secrets['access_key_secret'],
            self.get('RegionId'),
        )

def do_action(client, request):
    """
    Send Aliyun API request with client and return json result as a dict
    """
    resp = client.do_action_with_exception(request)
    return json.loads(resp.decode('utf-8'))


class BaseConfigParameterSelect(object):
    def show(self, config, client=None):
        click.echo(click.style('正在配置 ECS 实例的{} ...', fg='green').format(self.name))
        param = config.get(self.key)
        if param:
            msg = "检测到你上次所使用的{}是 {}, 是否保留这个设置， 还是重新选择? [保留 y/重选 n]".format(
                self.name, click.style(param, fg="magenta")
            )
            answer = click.prompt(msg, default='y').lower()
            if answer == 'y':
                return param

        request = self.request_cls()
        self.set_request_parameters(request)

        if client is None:
            client = config.create_api_client()
        api_result = do_action(client, request)
        items = self.items_getter(api_result)
        if getattr(self, 'select_sorting', None):
            items.sort(key=lambda x: x[self.select_sorting])
        select_list = '\n'.join('[{}] - {}'.format(
            idx, self.select_item_formatter(item)
        ) for idx, item in enumerate(items))
        msg = '可选的 {}:\n{}\n请选择实例的 {}（序号）'.format(self.name, select_list, self.name)
        idx = click.prompt(msg, type=int)
        param = items[idx][self.item_key]
        config.set(self.key, param)
        self.handle_selected_item(items[idx], config)

    def set_request_parameters(self, request):
        pass

    def handle_selected_item(self, item, config):
        pass

class RegionIdSelect(BaseConfigParameterSelect):
    name = "地域"
    key = "RegionId"
    request_cls = DescribeRegionsRequest.DescribeRegionsRequest
    items_getter = lambda self, x: x['Regions']['Region']
    item_key = "RegionId"
    select_item_formatter = lambda self, x: "{}({})".format(x['LocalName'], x['RegionId'])


class InstanceTypeSelect(BaseConfigParameterSelect):
    name = "实例规格"
    key = ['CreateInstanceParams', 'InstanceType']
    request_cls = DescribeInstanceTypesRequest.DescribeInstanceTypesRequest
    items_getter = lambda self, x: x['InstanceTypes']['InstanceType']
    item_key = "InstanceTypeId"
    select_item_formatter = lambda self, x: x['InstanceTypeId']

    def set_request_parameters(self, request):
        request.set_InstanceTypeFamily('ecs.gn5')

class SecurityGroupsSelect(BaseConfigParameterSelect):
    name = "安全组"
    key = ['CreateInstanceParams', 'SecurityGroupId']
    request_cls = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest
    items_getter = lambda self, x: x['SecurityGroups']['SecurityGroup']
    item_key = "SecurityGroupId"
    select_item_formatter = lambda self, x: "{}({})".format(x['SecurityGroupName'], x['SecurityGroupId'])

class DisksSelect(BaseConfigParameterSelect):
    name = "挂载的磁盘"
    key = 'DiskId'
    request_cls = DescribeDisksRequest.DescribeDisksRequest
    items_getter = lambda self, x: x['Disks']['Disk']
    item_key = "DiskId"
    select_item_formatter = lambda self, x: "{} {}G {}".format(x['DiskId'], x['Size'], x['Description'])

    def set_request_parameters(self, request):
        request.set_Portable('true')

    def handle_selected_item(self, item, config):
        config.set(('CreateInstanceParams', 'ZoneId'), item['ZoneId'])


class SnapshotsSelect(BaseConfigParameterSelect):
    name = "用于创建磁盘的快照"
    key = 'SnapshotId'
    request_cls = DescribeSnapshotsRequest.DescribeSnapshotsRequest
    items_getter = lambda self, x: x['Snapshots']['Snapshot']
    item_key = "SnapshotId"
    select_item_formatter = lambda self, x: "{} {} {}G".format(x['SnapshotId'], x['SnapshotName'], x['SourceDiskSize'])


class ZonesSelect(BaseConfigParameterSelect):
    name = "可用区"
    key = ['CreateInstanceParams', 'ZoneId']
    request_cls = DescribeZonesRequest.DescribeZonesRequest
    items_getter = lambda self, x: x['Zones']['Zone']
    item_key = "ZoneId"
    select_item_formatter = lambda self, x: "{} {}".format(x['ZoneId'], x['LocalName'])


class KeyPairsSelect(BaseConfigParameterSelect):
    name = "SSH 密钥对"
    key = ['CreateInstanceParams', 'KeyPairName']
    request_cls = DescribeKeyPairsRequest.DescribeKeyPairsRequest
    items_getter = lambda self, x: x['KeyPairs']['KeyPair']
    item_key = "KeyPairName"
    select_item_formatter = lambda self, x: x['KeyPairName']


class ImagesSelect(BaseConfigParameterSelect):
    name = "操作系统镜像"
    key = ['CreateInstanceParams', 'ImageId']
    request_cls = DescribeImagesRequest.DescribeImagesRequest
    items_getter = lambda self, x: x['Images']['Image']
    item_key = "ImageId"
    select_item_formatter = lambda self, x: x['OSName']
    select_sorting = 'OSName'

    def set_request_parameters(self, request):
        request.set_PageSize(50)
        request.set_OSType("linux")


def create_empty_disk(config):
    ZonesSelect().show(config=config)

    client = config.create_api_client()
    request = CreateDiskRequest.CreateDiskRequest()
    request.set_DiskName("ml-data-disk")
    request.set_DiskCategory("cloud_ssd")
    request.set_ZoneId(config.get(['CreateInstanceParams', 'ZoneId']))
    size = click.prompt('请设置你的磁盘大小, 单位 GB, 必须大于20:', default=30, type=int)
    request.set_Size(size)
    result = do_action(client, request)
    DiskId = result['DiskId']
    config.set('DiskId', DiskId)

def create_disk_from_snapshot(config):
    client = config.create_api_client()
    request = CreateDiskRequest.CreateDiskRequest()
    request.set_DiskName("ml-data-disk")
    request.set_DiskCategory("cloud_ssd")
    request.set_SnapshotId(config.get('SnapshotId'))
    request.set_ZoneId(config.get(['CreateInstanceParams', 'ZoneId']))
    result = do_action(client, request)
    DiskId = result['DiskId']
    config.set('DiskId', DiskId)


def wait_for_instance_status(config, status):
    """
    Wait for the instance's status to become the given status
    """
    client = config.create_api_client()
    InstanceId = config.get('InstanceId')
    while True:
        time.sleep(20)
        req = DescribeInstancesRequest.DescribeInstancesRequest()
        result = do_action(client, req)
        items = result["Instances"]["Instance"]
        lookups = {item['InstanceId']: item for item in items}
        if lookups[InstanceId]['Status'] == status:
            return
        else:
            click.echo("实例当前的状态为{}， 正在等待其变为 {} ...".format(
                lookups[InstanceId]['Status'], status
            ))


def wait_for_dick_status(config, status):
    client = config.create_api_client()
    DiskId = config.get('DiskId')
    while True:
        time.sleep(20)
        req = DescribeDisksRequest.DescribeDisksRequest()
        result = do_action(client, req)
        items = result['Disks']['Disk']
        lookups = {item['DiskId']: item for item in items}
        if lookups[DiskId]['Status'] == status:
            return
