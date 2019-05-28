#coding=utf8
import logging
import logging.config
import logging.handlers
import os
import stat
import sys
import inspect

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

logging.AUDIT = logging.INFO + 1
logging.addLevelName(logging.AUDIT, 'AUDIT')

_loggers = {}

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

def get_log_path():
    logpath = _get_log_file_path()
    if not os.path.exists(logpath):
        os.mknod(logpath)
    mode = int(options.logfile_mode, 8)
    st = os.stat(logpath)
    if st.st_mode != (stat.S_IFREG | mode):
        os.chmod(logpath, mode)

    return logpath

class Logger(object):

    def __init__(self, log_file_name, log_level, logger_name):

        #创建一个logger
        self.__logger = logging.getLogger(logger_name)

        #指定日志的最低输出级别，默认为WARN级别
        self.__logger.setLevel(log_level)

        #创建一个handler用于写入日志文件
        file_handler = logging.FileHandler(log_file_name)

        #创建一个handler用于输出控制台
        console_handler = logging.StreamHandler()

        #定义handler的输出格式
        formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(filename)s:%(lineno)d] - %(levelname)s: %(message)s')

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 给logger添加handler
        self.__logger.addHandler(file_handler)


    def get_log(self):
        return self.__logger


def getLogger(name='ops'):
    if options.debug == True:
        log_level = logging.DEBUG
    else:
        log_level = logging.info
    logpath = get_log_path()


    if name not in _loggers:
        LOG = Logger(logpath, log_level, name).get_log()
        _loggers[name] = LOG
    return _loggers[name]
