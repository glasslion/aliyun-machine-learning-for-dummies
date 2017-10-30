from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import os
from collections import OrderedDict
import time

import click
from aliyunsdkcore.client import AcsClient
from aliyunsdkecs.request.v20140526 import (DescribeDisksRequest,
                                            DescribeImagesRequest,
                                            DescribeInstancesRequest,
                                            DescribeInstanceTypesRequest,
                                            DescribeKeyPairsRequest,
                                            DescribeRegionsRequest,
                                            DescribeSecurityGroupsRequest)

CONFIG_FILE = 'config.json'


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
        except FileNotFoundError:
            pass

    def save(self):
        """
        Save configs into the config json file
        """
        with io.open(CONFIG_FILE, mode='w', encoding='utf-8') as f:
            return f.write(json.dumps(self._config, indent=4))

    def obtain_secret(self, name):
        """
        Obtain a secret config, and store it in self._secrets.
        Lookup the environment variables, if not found, then prompt to the user.
        """
        env_name = 'ALIYUN_{}'.format(name.upper())
        human_name = name.upper().replace('_', ' ')

        if os.environ.get(env_name):
            self._secrets[name] =os.environ.get(env_name)
        else:
            self._secrets[name] = click.prompt(
                'Please enter your {}'.format(human_name), type=str, hide_input=True)

    def set(self, key, value):
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
                node = node.get(k)
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

    def prompt(self):
        self.load()

        # We need a default region id to initialize the api client, then query other available regions
        default_region_id = 'cn-hangzhou'

        client = client = AcsClient(
            self._secrets['access_key_id'],
            self._secrets['access_key_secret'],
            default_region_id,
        )

        # Regions
        req = DescribeRegionsRequest.DescribeRegionsRequest()
        result = do_action(client, req)
        items = result['Regions']['Region']
        select_list = '\n'.join('[{}] - {}({})'.format(
            idx, item['LocalName'], item['RegionId']
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your region: \n{}\n'.format(select_list), type=int)
        RegionId = items[idx]['RegionId']
        self._config['RegionId'] = RegionId

        client = client = AcsClient(
            self._secrets['access_key_id'],
            self._secrets['access_key_secret'],
            RegionId,
        )

        if 'CreateInstanceParams' not in self._config:
            self._config['CreateInstanceParams'] = OrderedDict()

        # InstanceType
        req = DescribeInstanceTypesRequest.DescribeInstanceTypesRequest()
        req.set_InstanceTypeFamily('ecs.gn5')
        result = do_action(client, req)
        items = result['InstanceTypes']['InstanceType']
        select_list = '\n'.join('[{}] - {}'.format(
            idx, item['InstanceTypeId'],
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your Instance Type: \n{}\n'.format(select_list), type=int)
        InstanceTypeId = items[idx]['InstanceTypeId']
        self._config['CreateInstanceParams']['InstanceType'] = InstanceTypeId

        # SecurityGroup
        req = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest()
        result = do_action(client, req)
        items = result['SecurityGroups']['SecurityGroup']
        select_list = '\n'.join('[{}] - {}({})'.format(
            idx, item['SecurityGroupName'], item['SecurityGroupId']
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your security group: \n{}\n'.format(select_list), type=int)
        SecurityGroupId = items[idx]['SecurityGroupId']
        self._config['CreateInstanceParams']['SecurityGroupId'] = SecurityGroupId
        VpcId = items[idx]['VpcId']

        # Existing Disks
        req = DescribeDisksRequest.DescribeDisksRequest()
        req.set_Portable('true')
        result = do_action(client, req)
        items = result['Disks']['Disk']
        select_list = '\n'.join('[{}] - {} {}G {}'.format(
            idx, item['DiskId'], item['Size'], item['Description']
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your portable disk: \n{}\n'.format(select_list), type=int)
        DiskId = items[idx]['DiskId']
        self.set('DiskId', DiskId)
        ZoneId = items[idx]['ZoneId']
        self.set(('CreateInstanceParams', 'ZoneId'), ZoneId)

        # KeyPairName
        req = DescribeKeyPairsRequest.DescribeKeyPairsRequest()
        result = do_action(client, req)
        items = result['KeyPairs']['KeyPair']
        select_list = '\n'.join('[{}] - {}'.format(
            idx, item['KeyPairName'],
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your KeyPair Name: \n{}\n'.format(select_list), type=int)
        KeyPairName = items[idx]['KeyPairName']
        self._config['CreateInstanceParams']['KeyPairName'] = KeyPairName

        # Images
        req = DescribeImagesRequest.DescribeImagesRequest()
        req.set_PageSize(50)
        result = do_action(client, req)
        items = result['Images']['Image']
        items = sorted(items, key=lambda x: x['OSName'])
        select_list = '\n'.join('[{}] - {}'.format(
            idx, item['OSName'],
        ) for idx, item in enumerate(items))
        idx = click.prompt('Please select your Image(OS): \n{}\n'.format(select_list), type=int)
        ImageId = items[idx]['ImageId']
        self._config['CreateInstanceParams']['ImageId'] = ImageId

        InstanceName = click.prompt('Enter your ecs instance name:', default='ecs-ml-01', type=str)
        self._config['CreateInstanceParams']['InstanceName'] = InstanceName
        InternetChargeType = click.prompt('Enter your ecs Internet Charge Type:', default='PayByTraffic', type=str)
        self._config['CreateInstanceParams']['InternetChargeType'] = InternetChargeType
        SpotStrategy = click.prompt('Enter your spot strategy:', default='SpotWithPriceLimit', type=str)
        self._config['CreateInstanceParams']['SpotStrategy'] = SpotStrategy
        SpotPriceLimit = click.prompt('Enter your spot price limit', type=float)
        self._config['CreateInstanceParams']['SpotPriceLimit'] = SpotPriceLimit
        SpotPriceLimit = click.prompt('Enter your Internet max out bandwidth', type=int, default=5)
        self._config['CreateInstanceParams']['SpotPriceLimit'] = SpotPriceLimit
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
