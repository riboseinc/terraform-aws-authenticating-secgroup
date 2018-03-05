from contextlib import contextmanager
import json
import args
import model


@contextmanager
def get_catch(**kwargs):
    try:
        yield kwargs.get("default", None)
    except Exception as ex:
        pass


def handler(fn_handler, event):
    try:
        # dyna_sec_groups = Arguments.get().dyna_sec_groups(event)
        args.arguments.event = event
        failed_groups = fn_handler(model.DynaSecGroups())
    except Exception as error:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "cidr_ip": f"{args.arguments.cidr_ip}",
                "error": {
                    "message": str(error),
                    "type": error.__class__.__name__,
                    "args": error.args
                }
            })
        }

    return {
        "statusCode": 201 if not failed_groups else 200,
        "body": json.dumps({
            "success": True,
            "cidr_ip": f"{args.arguments.cidr_ip}",
            "failed_groups": failed_groups
        })
    }

class OperationNotSupportedError(Exception):
    pass


class NPE(Exception):
    pass


