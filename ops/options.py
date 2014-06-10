#coding=utf8

"""
every opt of used should bu define first


this options is based on tornado.options
"""

from tornado.options import define, parse_command_line,\
        parse_config_file, options

common_opts = [
        {
            "name": 'debug',
            "default": False,
            "help": 'if logged debug info',
            "type": bool,
        },
        {
            "name": 'verbose',
            "default": False,
            "help": 'if log detail',
            "type": bool,
        },
        {
            "name": 'config',
            "default": '/etc/ops/ops.conf',
            "help": 'path of config file',
            "type": str,
            "callback": lambda path: parse_config_file(path, final=False)
        },
        {
            "name": 'sql_connection',
            "default": 'mysql://ops:ops@localhost/ops?charset=utf8',
            "help": 'The SQLAlchemy connection string used to connect to \
                    the database',
            "type": str,
        },
        {
            "name": 'db_driver',
            "default": 'ops.db.api',
            "help": 'default db driver',
            "type": str,
        },
        {
            "name": 'lock_path',
            "default": '/var/lock',
            "help": 'path of config file',
            "type": str,
        },
        {
            "name": 'api_port',
            "default": 8080,
            "help": 'listen port of api',
            "type": int,
        },
        {
            "name": 'keystone_endpoint',
            "default": 'http://127.0.0.1:35357/v2.0',
            "help": 'the keystone endpoint url',
            "type": str,
        },
        {
            "name": "cached_backend",
            "default": 'redis://127.0.0.1:6379/0',
            "help": 'cached backend uri',
            "type": str,
        },
        ]


def register_opt(opt, group=None):
    """Register an option schema
    opt = {
            "name": 'config',
            "default": 'ops.conf',
            "help": 'path of config file',
            "tyle": str,
            "callback": lambda path: parse_config_file(path, final=False)
        }
    """
    if opt.get('name', ''):
        define(opt.pop('name'), **opt)


def register_opts(opts, group=None):
    """Register multiple option schemas at once."""
    for opt in opts:
        register_opt(opt, group)
    return options

def get_options(opts=None, group=None):
    if opts:
        register_opts(opts, group)
    options = register_opts(common_opts, 'common')
    parse_config_file(options.config, final=False)
    parse_command_line()
    return options

if __name__ == "__main__":
    print get_options().as_dict()
    options = get_options()
    print options.get('sql_connection', None)
