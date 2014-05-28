"""Session Handling for SQLAlchemy backend."""

import time

import sqlalchemy.interfaces
import sqlalchemy.orm
from sqlalchemy.exc import DisconnectionError, OperationalError
from sqlalchemy.pool import NullPool, StaticPool

from ops import exception


from ops.options import get_options

db_options = [

        {
            "name": 'sql_idle_timeout',
            "default": 3600,
            "help": 'timeout before idle sql connections are reaped',
            "type": int,
        },
        {
            "name": 'sql_connection_debug',
            "default": 0,
            "help": 'Verbosity of SQL debugging information. 0=None, '
                    '100=Everything',
            "type": int,
        },
        {
            "name": 'sql_max_retries',
            "default": 10,
            "help": 'maximum db connection retries during startup. '
                    '(setting -1 implies an infinite retry count)',
            "type": int,
        },
        {
            "name": 'sql_retry_interval',
            "default": 10,
            "help": 'interval between retries of opening a sql connection',
            "type": int,
        },
    ]

options = get_options(db_options, 'db')


_ENGINE = None
_MAKER = None


def get_session(autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy session."""
    global _MAKER

    if _MAKER is None:
        engine = get_engine()
        _MAKER = get_maker(engine, autocommit, expire_on_commit)

    session = _MAKER()
    session.query = exception.wrap_db_error(session.query)
    session.flush = exception.wrap_db_error(session.flush)
    return session

def model_query(*args, **kwargs):
    """
    :param session: if present, the session to use
    :param read_deleted: if read deleted data
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted')
    query = session.query(*args)

    if read_deleted == 'no':
        query = query.filter_by(deleted=False)
    elif read_deleted == 'only':
        query = query.filter_by(deleted=True)

    return query




class MySQLPingListener(object):

    """
    Ensures that MySQL connections checked out of the
    pool are alive.

    Borrowed from:
    http://groups.google.com/group/sqlalchemy/msg/a4ce563d802c929f
    """

    def checkout(self, dbapi_con, con_record, con_proxy):
        try:
            dbapi_con.cursor().execute('select 1')
        except dbapi_con.OperationalError, ex:
            if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
                LOG.warn('Got mysql server has gone away: %s', ex)
                raise DisconnectionError("Database server went away")
            else:
                raise


def is_db_connection_error(args):
    """Return True if error in connecting to db."""
    # NOTE(adam_g): This is currently MySQL specific and needs to be extended
    #               to support Postgres and others.
    conn_err_codes = ('2002', '2003', '2006')
    for err_code in conn_err_codes:
        if args.find(err_code) != -1:
            return True
    return False


def get_engine():
    """Return a SQLAlchemy engine."""
    global _ENGINE
    if _ENGINE is None:
        connection_dict = sqlalchemy.engine.url.make_url(options.sql_connection)

        engine_args = {
            "pool_recycle": options.sql_idle_timeout,
            "echo": False,
            'convert_unicode': True,
        }

        # Map our SQL debug level to SQLAlchemy's options
        if options.sql_connection_debug >= 100:
            engine_args['echo'] = 'debug'
        elif options.sql_connection_debug >= 50:
            engine_args['echo'] = True


        if 'mysql' in connection_dict.drivername:
            engine_args['listeners'] = [MySQLPingListener()]

        _ENGINE = sqlalchemy.create_engine(options.sql_connection, **engine_args)

        try:
            _ENGINE.connect()
        except OperationalError, e:
            if not is_db_connection_error(e.args[0]):
                raise

            remaining = options.sql_max_retries
            if remaining == -1:
                remaining = 'infinite'
            while True:
                msg = 'SQL connection failed. %s attempts left.'
                LOG.warn(msg % remaining)
                if remaining != 'infinite':
                    remaining -= 1
                time.sleep(options.sql_retry_interval)
                try:
                    _ENGINE.connect()
                    break
                except OperationalError, e:
                    if (remaining != 'infinite' and remaining == 0) or \
                       not is_db_connection_error(e.args[0]):
                        raise
    return _ENGINE


def get_maker(engine, autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy sessionmaker using the given engine."""
    return sqlalchemy.orm.sessionmaker(bind=engine,
                                       autocommit=autocommit,
                                       expire_on_commit=expire_on_commit)


def register_models(tables):
    """Register Models and create metadata.

    tablese = (Costlog,)

    """
    from sqlalchemy import create_engine
    models = tables
    engine = create_engine(options.sql_connection, echo=False)
    for model in models:
        model.metadata.create_all(engine)
