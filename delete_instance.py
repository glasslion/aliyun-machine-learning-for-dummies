import time

import click
from aliyunsdkecs.request.v20140526 import (DeleteInstanceRequest,
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
    cleanup(config)


def stop_instance(config):
    client = config.create_api_client()
    req = StopInstanceRequest.StopInstanceRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)


def delete_instance(config):
    client = config.create_api_client()
    req = DeleteInstanceRequest.DeleteInstanceRequest()
    req.set_InstanceId(config.get('InstanceId'))
    result = do_action(client, req)

def cleanup(config):
    config.pop("InstanceId")
    config.save()

if __name__ == '__main__':
    main()
