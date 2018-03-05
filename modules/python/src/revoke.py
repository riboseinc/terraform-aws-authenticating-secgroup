import helper


def handler(event=None, context=None):
    event.action = 'REVOKE'
    return helper.handler(fn_handler=lambda sg: sg.revoke(), event=event)
