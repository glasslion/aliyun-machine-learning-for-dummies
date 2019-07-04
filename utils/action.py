import json

def do_action(client, request):
    """
    Send Aliyun API request with client and return json result as a dict
    """
    resp = client.do_action_with_exception(request)
    return json.loads(resp.decode('utf-8'))
