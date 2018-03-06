from contextlib import contextmanager

import args
import json


@contextmanager
def catch(fn, pass_error=True, **kwargs):
    yield get_catch(fn=fn, pass_error=pass_error, **kwargs)


def get_catch(fn, pass_error=True, **kwargs):
    try:
        return fn()
    except Exception as error:
        return kwargs.get('default', None) if pass_error else error


def handler(fn_handler, action, event):
    args.arguments.event = event
    response = {
        "statusCode": 200,
        "body": {
            "action": action,
            "success": True,
            "cidr_ip": f"{args.arguments.cidr_ip}"
        }
    }

    try:
        import model
        succeed_groups, failed_groups = fn_handler(model.DynaSecGroups())
        if succeed_groups:
            response['body']['succeed_groups'] = succeed_groups

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

    response['body'] = json.dumps(response['body'])
    return response


def return_if(**kwargs):
    def wrap(func):
        def wrapped_func(obj, *func_args, **func_kwargs):
            has_attr = kwargs.get('has_attr', None)
            if has_attr and hasattr(obj, has_attr):
                return_attr = kwargs.get('return_attr', None)
                if return_attr and hasattr(obj, return_attr): return getattr(obj, return_attr)
                return getattr(obj, has_attr)
            return func(obj, *func_args, **func_kwargs)

        return wrapped_func

    return wrap


class OperationNotSupportedError(Exception):
    pass


class NPE(Exception):
    pass
