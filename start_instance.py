# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import json

# Due to a bug in the aliyun sdk, https://github.com/aliyun/aliyun-openapi-python-sdk/issues/43
# this import must appear before any aliyun sdk imports
from utils import Config, do_action, wait_for_instance_status

import io
import click
click.disable_unicode_literals_warning
from aliyunsdkecs.request.v20140526 import (AllocatePublicIpAddressRequest,
                                            AttachDiskRequest,
                                            CreateInstanceRequest,
                                            DescribeInstancesRequest,
                                            StartInstanceRequest)


@click.command()
@click.option(
    '--interactive', '-i', default=False, is_flag=True,
    help='Interactive mode，allow user to input/select ecs instance parameters interactively')
def main(interactive):
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')
    if interactive:
        config.config_via_prompt()
    else:
        config.load()

    should_create_new = True
    if config.get('InstanceId'):
        answer = click.prompt("Found an existing instance, still create a new one? [y/n]")
        if answer.lower() == 'n':
            should_create_new = False
    if should_create_new:
        create_instance(config)

    allocate_public_ip(config)
    attach_disk(config)
    wait_for_instance_status(config, "Stopped")
    start_instance(config)
    save_instance_info(config)


def create_instance(config):
    click.echo(click.style("正在创建实例 ...", fg="green"))
    client = config.create_api_client()
    req = CreateInstanceRequest.CreateInstanceRequest()

    create_params = config.get('CreateInstanceParams')
    if create_params:
        for param_name, param_value in create_params.items():
            setter = getattr(req, 'set_'+param_name)
            setter(param_value)

    result = do_action(client, req)
    instance_id = result['InstanceId']
    config.set('InstanceId', instance_id)
    config.save()
    return instance_id

def allocate_public_ip(config):
    click.echo(click.style("正在分配公网 IP ...", fg="green"))
    client = config.create_api_client()
    req = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)


def start_instance(config):
    click.echo(click.style("正在启动实例 ...", fg="green"))
    client = config.create_api_client()
    req = StartInstanceRequest.StartInstanceRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)

def attach_disk(config):
    click.echo(click.style("正在挂载数据盘 ...", fg="green"))
    client = config.create_api_client()
    req = AttachDiskRequest.AttachDiskRequest()
    req.set_InstanceId(config.get('InstanceId'))
    req.set_DiskId(config.get('DiskId'))
    result = do_action(client, req)


def save_instance_info(config):
    client = config.create_api_client()
    req = DescribeInstancesRequest.DescribeInstancesRequest()
    req.set_InstanceIds(json.dumps([config.get('InstanceId')]))
    result = do_action(client, req)
    items = result["Instances"]["Instance"]
    lookups = {item['InstanceId']: item for item in items}
    InstanceId = config.get('InstanceId')
    PublicIpAddress = lookups[InstanceId]['PublicIpAddress']['IpAddress'][0]
    config.set('PublicIpAddress', PublicIpAddress)
    update_playbook_hosts(config)
    print("Instance public ip: {}".format(PublicIpAddress))


def update_playbook_hosts(config):
    with io.open("playbook/hosts", "w") as f:
        f.write("[gpu-instance]\n")
        f.write(config.get('PublicIpAddress'))


if __name__ == '__main__':
    main()
