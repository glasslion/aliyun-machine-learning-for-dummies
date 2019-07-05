import os
import time

from aliyunsdkecs.request.v20140526 import (
    CreateSecurityGroupRequest,
    DescribeSecurityGroupsRequest,
    AuthorizeSecurityGroupRequest,
    CreateVpcRequest,
    CreateVSwitchRequest,
    DescribeVSwitchesRequest,
    DescribeKeyPairsRequest,
    ImportKeyPairRequest,
)

from .action import do_action
from .select import BaseConfigParameterSelect


class SecurityGroupsSelect(BaseConfigParameterSelect):
    name = "安全组"
    key = ['CreateInstanceParams', 'SecurityGroupId']
    request_cls = DescribeSecurityGroupsRequest.DescribeSecurityGroupsRequest
    items_getter = lambda self, x: x['SecurityGroups']['SecurityGroup']
    item_key = "SecurityGroupId"
    select_item_formatter = lambda self, x: "{}({})".format(x['SecurityGroupName'], x['SecurityGroupId'])

    def handle_selected_item(self, item):
        self.set_VSwitchId(item['VpcId'])

    def fix_empty_items(self):
        # 因为创建安全组时需要指定 VpcId, 这里偷个懒， 假定安全组为空时， vpc 和 vswitch
        # 也为空， 创建一个新的
        print('正在创建 VPC 请稍等 ...')
        self.create_vpc()
        print('正在创建 VSwitch 请稍等 ...')
        time.sleep(5)
        self.create_vswitch()
        print('正在创建 安全组 请稍等 ...')
        self.create_sg()
        time.sleep(5)
        self.add_sg_rule()

    def create_sg(self):
        request = CreateSecurityGroupRequest.CreateSecurityGroupRequest()
        request.set_VpcId(self.VpcId)
        result = do_action(self.client, request)
        self.SecurityGroupId = result['SecurityGroupId']

    def add_sg_rule(self):
        # 增加一条安全组入方向规则
        request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
        request.set_IpProtocol("tcp")
        request.set_PortRange("8880/8888")
        request.set_SecurityGroupId(self.SecurityGroupId)
        request.set_SourceCidrIp('0.0.0.0/0')

    def create_vpc(self):
        request = CreateVpcRequest.CreateVpcRequest()
        request.set_VpcName('ml-auto-vpc')
        request.set_CidrBlock('192.168.0.0/16')
        result = do_action(self.client, request)
        self.VpcId = result['VpcId']

    def create_vswitch(self):
        request = CreateVSwitchRequest.CreateVSwitchRequest()
        request.set_CidrBlock('192.168.0.0/24')
        request.set_VpcId(self.VpcId)
        ZoneId = self.config.get(['CreateInstanceParams', 'ZoneId'])
        request.set_ZoneId(ZoneId)
        result = do_action(self.client, request)

    def set_VSwitchId(self, vpc_id):
        request = DescribeVSwitchesRequest.DescribeVSwitchesRequest()
        request.set_VpcId(self.VpcId)
        result = do_action(self.client, request)
        item = result['VSwitches']['VSwitch'][0]
        self.config.set(['CreateInstanceParams', 'VSwitchId'], item['VSwitchId'])


class KeyPairsSelect(BaseConfigParameterSelect):
    name = "SSH 密钥对"
    key = ['CreateInstanceParams', 'KeyPairName']
    request_cls = DescribeKeyPairsRequest.DescribeKeyPairsRequest
    items_getter = lambda self, x: x['KeyPairs']['KeyPair']
    item_key = "KeyPairName"
    select_item_formatter = lambda self, x: x['KeyPairName']

    def fix_empty_items(self):
        self.import_key()

    def import_key(self):
        request = ImportKeyPairRequest.ImportKeyPairRequest()
        request.set_KeyPairName('ml-sshkey')
        key_path = os.path.expanduser('~/.ssh/id_rsa.pub')
        with open(key_path) as f:
            keybody = f.read()

        request.set_PublicKeyBody(keybody)
        do_action(self.client, request)
