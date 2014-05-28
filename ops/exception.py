
class OpsException(Exception):
    """Base Ops Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = "An unknown exception occurred."
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, **kwargs):
        self.kwargs = kwargs

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass

        if not message:
            try:
                message = self.message % kwargs

            except Exception as e:
                # at least get the core message out if something happened
                message = self.message

        super(OpsException, self).__init__(message)


class Duplicate(OpsException):
        pass

def wrap_db_error(f):
    def _wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except UnicodeEncodeError:
            raise InvalidUnicodeParameter()
        except Exception, e:
            LOG.exception('DB exception wrapped.')
            raise DBError(e)
    _wrap.func_name = f.func_name
    return _wrap

class NotFound(OpsException):
    message = "Resource could not be found."
    code = 404

class ServiceNotFound(NotFound):
    message = "Service %(service_id)s could not be found."
