import json
from helper import Rule, SecGroup


def handler(event=None, context=None):
    handle_type = "${type}"

    if handle_type not in ['ingress', 'egress']:
        return {
            "statusCode": 404,
            "body": json.dumps({"success": False, "error": f"Not found handler for type {handle_type.upper()}"})
        }

    has_created = True

    try:
        cidr_ip = event['requestContext']['identity']['sourceIp'] + '/32'
        security_groups = json.loads('${security_groups}')

        rule = Rule(cidr_ip=cidr_ip)

        for group in security_groups:
            sec_group = SecGroup(group_id=group, rule=rule)
            has_created = sec_group.authorize_ingress() if handle_type == 'ingress' else sec_group.authorize_egress()

    except Exception as error:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": {"message": str(error), "type": error.__class__.__name__, "args": error.args}
            })
        }

    return {
        "statusCode": 201 if has_created else 200,
        "body": json.dumps({"success": True, "code": "CREATED" if has_created else "UPDATED"})
    }
