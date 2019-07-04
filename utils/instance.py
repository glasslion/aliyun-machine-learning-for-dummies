import time
import click

from aliyunsdkecs.request.v20140526 import (
    DescribeInstanceTypesRequest,
    DescribeInstancesRequest,
)

from .action import do_action
from .select import BaseConfigParameterSelect


class InstanceTypeSelect(BaseConfigParameterSelect):
    name = "实例规格"
    key = ['CreateInstanceParams', 'InstanceType']
    request_cls = DescribeInstanceTypesRequest.DescribeInstanceTypesRequest
    items_getter = lambda self, x: x['InstanceTypes']['InstanceType']
    item_key = "InstanceTypeId"
    select_item_formatter = lambda self, x: x['InstanceTypeId']

    def set_request_parameters(self, request):
        # other common instace type are: gn5i, sn2, sn1
        request.set_InstanceTypeFamily('ecs.c5')


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
