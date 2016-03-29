"""Nova logging handler.

This module adds to logging functionality by adding the option to specify
a context object when calling the various log methods.  If the context object
is not specified, default formatting is used.

It also allows setting of formatting information through flags.

"""

import cStringIO
import inspect
import itertools
import json
import logging
import logging.config
import logging.handlers
import os
import stat
import sys
import traceback

from ops.options import get_options

service_opts = [
    {
        "name": 'log_config',
        "default": '',
        "help": 'log config file',
        "type": str,
    },
    {
        "name": 'log_dir',
        "default": '/var/log/ops',
        "help": 'the dir to store log file',
        "type": str,
    },
    {
        "name": 'log_file',
        "default": '',
        "help": 'the file use to store log',
        "type": str,
    },
    {
        "name": 'log_format',
        "default": '%(asctime)s %(levelname)8s [%(name)s] %(message)s',
        "help": 'time format of log',
        "type": str,
    },
    {
        "name": 'log_date_format',
        "default": '%Y-%m-%d %H:%M:%S',
        "help": 'time format of log',
        "type": str,
    },
    {
        "name": 'logfile_mode',
        "default": '0644',
        "help": 'Default file mode used when creating log files',
        "type": str,
    },
    ]

options = get_options(service_opts, 'services')

# our new audit level
# NOTE(jkoelker) Since we synthesized an audit level, make the logging
#                module aware of it so it acts like other levels.
logging.AUDIT = logging.INFO + 1
logging.addLevelName(logging.AUDIT, 'AUDIT')


try:
    NullHandler = logging.NullHandler
except AttributeError:  # NOTE(jkoelker) NullHandler added in Python 2.7
    class NullHandler(logging.Handler):
        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None


def _get_binary_name():
    return os.path.basename(inspect.stack()[-1][1])


def _get_log_file_path(binary=None):
    logfile = options.log_file
    logdir = options.log_dir

    if logfile and not logdir:
        return logfile

    if logfile and logdir:
        return os.path.join(logdir, logfile)

    if logdir:
        binary = binary or _get_binary_name()
        return '%s.log' % (os.path.join(logdir, binary),)


class OpsLogAdapter(logging.LoggerAdapter):
    warn = logging.LoggerAdapter.warning

    def __init__(self, logger):
        self.logger = logger

    def audit(self, msg, *args, **kwargs):
        self.log(logging.AUDIT, msg, *args, **kwargs)

    def process(self, msg, kwargs):
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        extra = kwargs['extra']
        extra['extra'] = extra.copy()
        return msg, kwargs


def handle_exception(type, value, tb):
    extra = {}
    if options.verbose:
        extra['exc_info'] = (type, value, tb)
    getLogger().critical(str(value), **extra)


def setup():
    """Setup ops logging."""
    sys.excepthook = handle_exception

    if options.log_config:
        try:
            logging.config.fileConfig(options.log_config)
        except Exception:
            traceback.print_exc()
            raise
    else:
        _setup_logging_from_flags()


def _setup_logging_from_flags():
    ops_root = getLogger().logger
    for handler in ops_root.handlers:
        ops_root.removeHandler(handler)

    logpath = _get_log_file_path()
    if logpath:
        filelog = logging.handlers.WatchedFileHandler(logpath)
        ops_root.addHandler(filelog)

        mode = int(options.logfile_mode, 8)
        st = os.stat(logpath)
        if st.st_mode != (stat.S_IFREG | mode):
            os.chmod(logpath, mode)

    for handler in ops_root.handlers:
        handler.setFormatter(logging.Formatter(fmt=options.log_format,
            datefmt=options.log_date_format))

    if options.verbose or options.debug:
        ops_root.setLevel(logging.DEBUG)
    else:
        ops_root.setLevel(logging.INFO)

    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)
    handler = NullHandler()
    handler.setFormatter(logging.Formatter())
    root.addHandler(handler)


_loggers = {}


def getLogger(name='ops'):
    if name not in _loggers:
        _loggers[name] = OpsLogAdapter(logging.getLogger(name))
    return _loggers[name]
