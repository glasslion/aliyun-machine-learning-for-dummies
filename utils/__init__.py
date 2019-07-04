# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import os
import logging
from collections import OrderedDict
import time

import click
import six
from tenacity import retry, after_log,stop_after_attempt, wait_exponential
from aliyunsdkcore.client import AcsClient

from .action import do_action
from .select import BaseConfigParameterSelect
from .region import RegionIdSelect, ZonesSelect
from .instance import InstanceTypeSelect, wait_for_instance_status
from .disk import (
    DisksSelect, SnapshotsSelect, ImagesSelect, create_empty_disk,
    create_disk_from_snapshot, wait_for_dick_status)
from .security import SecurityGroupsSelect, KeyPairsSelect


logger = logging.getLogger(__name__)


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
            click.echo("Can not find the config.json file.")

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

    def obtain_secrets(self):
        self.obtain_secret('access_key_id')
        self.obtain_secret('access_key_secret')

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

        msg = "ECS实例自带的磁盘， 在实例被删除后， 也会被删除。为了保存你的工作， 你需要额外再挂载一块磁盘。\
你可以选择是创建一块全新的磁盘(n)， 还是重用现有的一块磁盘(e)，或者是使用快照创建一块新的磁盘(s), [n/e/s]"
        answer = click.prompt(msg).lower()
        if answer == 'n':
            ZonesSelect().show(config=self)
            create_empty_disk(config=self)
        elif answer == 'e':
            DisksSelect().show(config=self)
        else:
            ZonesSelect().show(config=self)
            SnapshotsSelect().show(config=self)
            create_disk_from_snapshot(config=self)
        SecurityGroupsSelect().show(config=self)
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

    def create_api_client(self, region_id=None):
        if region_id is None:
            region_id = self.get('RegionId')
        return AcsClient(
            self._secrets['access_key_id'],
            self._secrets['access_key_secret'],
            region_id,
        )


