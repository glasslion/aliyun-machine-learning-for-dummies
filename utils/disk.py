import time
import click

from aliyunsdkecs.request.v20140526 import (
    DescribeDisksRequest,
    DescribeSnapshotsRequest,
    DescribeImagesRequest,
    CreateDiskRequest,
)

from .action import do_action
from .select import BaseConfigParameterSelect


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


class ImagesSelect(BaseConfigParameterSelect):
    name = "操作系统镜像"
    key = ['CreateInstanceParams', 'ImageId']
    request_cls = DescribeImagesRequest.DescribeImagesRequest
    items_getter = lambda self, x: x['Images']['Image']
    item_key = "ImageId"
    select_item_formatter = lambda self, x: "{} {}".format(x['OSName'], x['Description'])
    select_sorting = 'OSName'

    def set_request_parameters(self, request):
        request.set_PageSize(50)
        request.set_OSType("linux")


def create_empty_disk(config):
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
