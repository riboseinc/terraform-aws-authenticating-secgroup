import json
from model import DynaSecGroups
import helper


def handler(event=None, context=None):
    try:
        dyna_sec_groups = DynaSecGroups(event)
        revoked, _ = dyna_sec_groups.clear()
    except Exception as error:
        status_code = 500
        if isinstance(error, helper.OperationNotSupportedError):
            status_code = 404

        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": False,
                "error": {"message": str(error), "type": error.__class__.__name__, "args": error.args}
            })
        }

    partial_revoke_msg = f"Some  expired IPs in security_groups {dyna_sec_groups.security_groups}"
    revoke_msg = f"Revoke all expired IPs in security_groups {dyna_sec_groups.security_groups}"
    return {
        "statusCode": 200 if revoked else 201,
        "body": json.dumps({
            "success": True,
            "code": "REVOKED" if revoked else "PARTIAL_REVOKED",
            "message": revoke_msg if revoked else partial_revoke_msg
        })
    }
