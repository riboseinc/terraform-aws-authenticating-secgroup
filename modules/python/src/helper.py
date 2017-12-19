from contextlib import contextmanager


@contextmanager
def catch(*exceptions, **kwargs):
    try:
        yield kwargs.get("default", None)
    except exceptions or Exception:
        pass


class OperationNotSupportedError(Exception):
    pass
