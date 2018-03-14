import helper


def handler(event=None, context=None):
    return helper.handler(fn_handler=lambda sg: sg.authorize(), action='AUTHORIZE', event=event)
