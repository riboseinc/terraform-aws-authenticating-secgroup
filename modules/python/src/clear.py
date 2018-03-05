import helper


def handler(event=None, context=None):
    event.action = 'CLEAR'
    return helper.handler(fn_handler=lambda sg: sg.clear(), event=event)
