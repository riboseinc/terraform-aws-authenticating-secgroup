from contextlib import contextmanager

import args
import model


@contextmanager
def catch(fn, pass_error=True, **kwargs):
    yield get_catch(fn=fn, pass_error=pass_error, **kwargs)


def get_catch(fn, pass_error=True, **kwargs):
    try:
        return fn()
    except Exception as error:
        return kwargs.get('default', None) if pass_error else error


def handler(fn_handler, event):
    args.arguments.event = event
    response = {
        "statusCode": 200,
        "action": event.action,
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
