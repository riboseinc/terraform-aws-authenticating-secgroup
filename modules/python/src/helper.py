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
            if error:
                error_groups.append({
                    'group_id': sec_group.aws_group_id,
                    'error': str(error)
                })
            elif sec_group.error_rules:
                error_groups.append({
                    'group_id': sec_group.aws_group_id,
                    'rules': [{
                        'type_from_to': f'{r.type}_{r.from_port}_{r.to_port}',
                        'error': str(r.error)
                    } for r in sec_group.error_rules]
                })

        if error_groups:
            response['body']['error'] = {
                'message': 'Some errors occurred when sending commands to AWS',
                'groups': error_groups
            }
            response['statusCode'] = 206  # partial groups succeed
    except exceptions.ClientError as error:
        response['statusCode'] = 500
        response['body']['success'] = False
        response['body']['error'] = str(error)

    response['body'] = json.dumps(response['body'])
    return response


def try_json_loads(json_str):
    if len(json_str) == 0:
        return None

    try:
        return json.loads(json_str)
    except json.decoder.JSONDecodeError:
        return try_json_loads(json_str[1:-1])


class OperationNotSupportedError(Exception):
    pass
