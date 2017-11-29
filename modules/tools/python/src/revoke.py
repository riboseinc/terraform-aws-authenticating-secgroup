import json
from helper import Rule, SecGroup


def handler(event, context):
    handle_type = "${type}"
    if handle_type == 'ingress':
        return handle_ingress(event=event, context=context)
    elif handle_type == 'egress':
        return handle_egress(event=event, context=context)

    return {
        "statusCode": 404,
        "body": json.dumps({"success": False, "error": f"Not found handler for type {handle_type.upper()}"})
    }


def handle_ingress(event, context):
    pass


def handle_egress(event, context):
    pass
