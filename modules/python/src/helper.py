import args
import json


def get_catch(fn, ignore_error=True, ignore_result=False, default=None, **kwargs):
    try:
        result = fn(**kwargs)
        return None if ignore_result else result
    except Exception as error:
        return default if ignore_error else error


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
        failed_groups = fn_handler(model.DynaSecGroups())
        # if succeed_groups:
        #     response['body']['succeed_groups'] = succeed_groups

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


# def return_if(**kwargs):
#     def wrap(func):
#         def wrapped_func(obj, *func_args, **func_kwargs):
#             has_attr = kwargs.get('has_attr', None)
#             if has_attr and hasattr(obj, has_attr):
#                 return_attr = kwargs.get('return_attr', None)
#                 if return_attr and hasattr(obj, return_attr): return getattr(obj, return_attr)
#                 return getattr(obj, has_attr)
#
#             error_handler = kwargs.get('error_handler', None)
#             try:
#                 return func(obj, *func_args, **func_kwargs)
#             except Exception as error:
#                 if error_handler and hasattr(obj, error_handler):
#                     return getattr(obj, error_handler)(error, *func_args, **func_kwargs)
#                 else:
#                     raise error
#
#         return wrapped_func
#
#     return wrap


def json_array_strip(json_str):
    j = json_str.find("[")
    k = json_str.rfind("]") + 1
    return json_str[j:k]


class OperationNotSupportedError(Exception):
    pass


class AwsApiError(Exception):
    pass
