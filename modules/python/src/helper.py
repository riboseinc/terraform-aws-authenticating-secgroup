import args
import json
import model
import boto3
from botocore import exceptions
from itertools import groupby


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
        sec_groups = []
        region_rules = groupby(args.arguments.security_groups, lambda r: r['region_name'])
        for region_name, security_groups in region_rules:
            security_groups = [sg for sg in security_groups]
            group_ids = list(map(lambda sg: sg['group_id'], security_groups))

            ec2 = boto3.resource('ec2', region_name=region_name)
            result_set = ec2.meta.client.describe_security_groups(Filters=[{'Name': 'group-id', 'Values': group_ids}])
            if not result_set['SecurityGroups']: continue

            sec_groups += [model.SecGroup(
                aws_client=ec2.meta.client,
                aws_group_dict=aws_group_dict,
                rules=next(filter(lambda sg: sg['group_id'] == aws_group_dict['GroupId'], security_groups))['rules'])
                for aws_group_dict in result_set['SecurityGroups']]

        error_groups = []
        for sec_group in sec_groups:
            error = get_catch(fn=lambda: fn_handler(sec_group), ignore_error=False, ignore_result=True)
            if error: error_groups.append((error, sec_group))

        if error_groups:
            response['body']['errors'] = [{'error': str(eg[0]), 'group_id': eg[1].aws_group_id} for eg in error_groups]
            response['statusCode'] = 206  # partial groups succeed
    except exceptions.ClientError as error:
        response['statusCode'] = 500
        response['body']['success'] = False
        response['body']['error'] = str(error)

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
