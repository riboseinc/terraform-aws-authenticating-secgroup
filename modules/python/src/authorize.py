import json
from model import DynaSecGroups
import helper


def handler(event=None, context=None):
    try:
        dyna_sec_groups = DynaSecGroups(event)
        has_created, _ = dyna_sec_groups.authorize()
    except Exception as error:
        status_code = 500
        if isinstance(error, helper.OperationNotFoundError):
            status_code = 404

        return {
            "statusCode": status_code,
            "body": json.dumps({
                "success": False,
                "error": {"message": str(error), "type": error.__class__.__name__, "args": error.args}
            })
        }

    return {
        "statusCode": 201 if has_created else 200,
        "body": json.dumps({
            "success": True,
            "code": "CREATED" if has_created else "UPDATED",
            "message": f"{dyna_sec_groups.cidr_ip} added to groups {dyna_sec_groups.security_groups}"
        })
    }
