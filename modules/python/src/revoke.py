import json
from model import DynaSecGroups
import helper


def handler(event=None, context=None):
    try:
        dyna_sec_groups = DynaSecGroups(event)
        revoked, fail_groups = dyna_sec_groups.revoke()
    except Exception as error:
        status_code = 404 if isinstance(error, helper.OperationNotSupportedError) else 500
        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": False,
                "cidr_ip": f"{dyna_sec_groups.cidr_ip}",
                "security_groups": dyna_sec_groups.security_groups,
                "error": {"message": str(error), "type": error.__class__.__name__, "args": error.args}
            })
        }

    fail_message = f"{dyna_sec_groups.cidr_ip} not found"
    success_message = f"{dyna_sec_groups.cidr_ip} revoked"
    return {
        "statusCode": 200 if revoked else 404,
        "body": json.dumps({
            "success": revoked,
            "code": "REVOKED" if revoked else "SOURCE_IP_NOT_FOUND",
            "cidr_ip": f"{dyna_sec_groups.cidr_ip}",
            "security_groups": dyna_sec_groups.security_groups,
            "message": fail_message if not revoked else success_message
        })
    }
