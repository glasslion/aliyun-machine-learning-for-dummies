# -*- coding: utf-8 -*-
import time

import click
from aliyunsdkecs.request.v20140526 import (DeleteInstanceRequest,
                                            DeleteSnapshotRequest,
                                            DeleteDiskRequest,
                                            CreateSnapshotRequest,
                                            StopInstanceRequest)
from utils import Config, do_action, wait_for_instance_status

def main():
    config = Config()
    config.obtain_secret('access_key_id')
    config.obtain_secret('access_key_secret')
    config.load()

    stop_instance(config)
    wait_for_instance_status(config, "Stopped")
    delete_instance(config)
    answer = click.prompt("是否要为当前的数据盘创建一个快照, 然后删除数据盘， 以节约费用? [y/n]")
    if answer == 'y':
        OldSnapshotId = config.get('SnapshotId')
        create_snapshot(config)
        delete_disk(config)
        if OldSnapshotId:
            delete_snapshot(config, OldSnapshotId)

    cleanup(config)


def stop_instance(config):
    click.echo(click.style("正在停止实例 ...", fg="green"))
    client = config.create_api_client()
    req = StopInstanceRequest.StopInstanceRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)


def delete_instance(config):
    click.echo(click.style("正在删除实例 ...", fg="green"))
    client = config.create_api_client()
    req = DeleteInstanceRequest.DeleteInstanceRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)

def create_snapshot(config):
    client = config.create_api_client()
    request = CreateSnapshotRequest.CreateSnapshotRequest()
    request.set_DiskId(config.get('DiskId'))
    result = do_action(client, request)
    SnapshotId= result['SnapshotId']
    config.set('SnapshotId', SnapshotId)

def delete_snapshot(config, snapshot_id):
    client = config.create_api_client()
    request = DeleteSnapshotRequest.DeleteSnapshotRequest()
    request.set_SnapshotId(snapshot_id)
    do_action(client, request)

def delete_disk(config):
    client = config.create_api_client()
    request = DeleteDiskRequest.DeleteDiskRequest()
    request.set_DiskId(config.get('DiskId'))
    do_action(client, request)
    config.pop("DiskId")




def cleanup(config):
    click.echo(click.style("正在更新配置文件 ...", fg="green"))
    config.pop("InstanceId")
    config.save()

if __name__ == '__main__':
    main()
