import helper


def handler(event=None, context=None):
    event.action = 'AUTHORIZE'
    return helper.handler(fn_handler=lambda sg: sg.authorize(), event=event)
