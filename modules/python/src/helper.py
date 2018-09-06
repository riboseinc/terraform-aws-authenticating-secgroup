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

    status_code = 200
    success = True
    response_errors = []

    existing_sec_groups = []
    not_found_groups = []

    response_403 = {
        "statusCode": 403,
        "body": json.dumps({
            "action": action,
            "success": False,
            "cidr_ip": f"{args.arguments.cidr_ip}"
        })
    }
    try:
        if args.arguments.api_caller not in args.arguments.accessible_users:
            return response_403
    except exceptions.ClientError as error:
        args.arguments.logger.error(str(error))
        return response_403

    try:
        region_rules = groupby(args.arguments.security_groups, lambda r: r['region_name'])
        for region_name, security_groups in region_rules:
            security_groups = [sg for sg in security_groups]
            group_ids = list(map(lambda sg: sg['group_id'], security_groups))

            ec2 = boto3.resource('ec2', region_name=region_name)
            result_set = ec2.meta.client.describe_security_groups(Filters=[{'Name': 'group-id', 'Values': group_ids}])
            if not result_set['SecurityGroups']:
                not_found_groups += group_ids
                continue

            found_groups = [model.SecGroup(
                aws_client=ec2.meta.client,
                aws_group_dict=aws_group_dict,
                rules=next(filter(lambda sg: sg['group_id'] == aws_group_dict['GroupId'], security_groups))['rules'])
                for aws_group_dict in result_set['SecurityGroups']]
            existing_sec_groups += found_groups

            not_found_groups += list(set(group_ids) - set(list(map(lambda g: g.aws_group_id, found_groups))))

        errors = []
        for sec_group in existing_sec_groups:
            error = get_catch(fn=lambda: fn_handler(sec_group), ignore_error=False, ignore_result=True)
            if error:
                errors.append({
                    'group_id': sec_group.aws_group_id,
                    'message': str(error)
                })
            elif sec_group.error_rules:
                errors.append({
                    'group_id': sec_group.aws_group_id,
                    'rules': [{
                        'type_from_to': f'{r.type}_{r.from_port}_{r.to_port}',
                        'message': r.error
                    } for r in sec_group.error_rules]
                })

        if not existing_sec_groups:
            response_errors.append({
                'message': 'There is no group found => Ignore the action',
                'details': f'Security groups input: {args.arguments.origin_security_groups}'
            })

        if errors:
            response_errors.append({
                'message': 'Some errors occurred when sending commands to AWS',
                'details': errors
            })
            status_code = 206  # partial groups succeed
    except exceptions.ClientError as error:
        status_code = 500
        success = False
        response_errors.append({"message": "Server error", "details": str(error)})

    args.arguments.logger.debug(f"not_found_groups: {not_found_groups}")
    if not_found_groups:
        response_errors.append({
            "message": "Unable to find some groups",
            "details": not_found_groups
        })

    response = {
        "statusCode": status_code,
        "body": {
            "action": action,
            "success": success,
            "cidr_ip": f"{args.arguments.cidr_ip}"
        }
    }
    if response_errors:
        response['body']['errors'] = response_errors

    response['body'] = json.dumps(response['body'])
    return response


def json_loads(json_str):
    try:
        return json.loads(json_str) if json_str else None
    except json.JSONDecodeError as e:
        args.arguments.logger.debug(f"json_loads error: {e}")
    return json_loads(json_str[1:-1])


class OperationNotSupportedError(Exception):
    pass
