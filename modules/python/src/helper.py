from contextlib import contextmanager
import json
import args
import model


@contextmanager
def get_catch(**kwargs):
    try:
        yield kwargs.get("default", None)
    except Exception as ex:
        pass


def handler(fn_handler, event):
    args.arguments.event = event
    response = {
        "statusCode": 200,
        "body": {
            "success": True,
            "cidr_ip": f"{args.arguments.cidr_ip}"
        }
    }

    try:
        failed_groups = fn_handler(model.DynaSecGroups())
        if failed_groups:
            response['body']['failed_groups'] = failed_groups
            response['statusCode'] = 206  # partial groups succeed
    except Exception as error:
        response['statusCode'] = 500
        response['body']['success'] = False
        response['body']['error'] = {
            "message": str(error),
            "type": error.__class__.__name__,
            "args": error.args
        }

    return response


class OperationNotSupportedError(Exception):
    pass


class NPE(Exception):
    pass
