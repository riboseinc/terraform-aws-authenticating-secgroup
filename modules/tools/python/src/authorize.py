import json
from helper import DynaSecGroups
from botocore.model import OperationNotFoundError


def handler(event=None, context=None):
    try:
        has_created, _ = DynaSecGroups(event).authorize()
    except Exception as error:
        status_code = 500
        if isinstance(error, OperationNotFoundError):
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
            "code": "CREATED" if has_created else "UPDATED"
        })
    }
