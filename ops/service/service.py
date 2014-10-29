"""Generic Node base class for all workers that run on hosts."""

import inspect
import os
import socket

import eventlet
import greenlet

from ops.service import db
from ops import exception
from ops import log as logging
from ops import utils

from ops.options import get_options

LOG = logging.getLogger(__name__)

service_opts = [
    {
        "name": 'report_interval',
        "default": 30,
        "help": 'seconds between nodes reporting state to datastore',
        "type": int,
    },
    {
        "name": 'periodic_interval',
        "default": 60,
        "help": 'seconds between running periodic tasks',
        "type": int,
    },
    ]

options = get_options(service_opts, 'services')


class Launcher(object):
    """Launch one or more services and wait for them to complete."""

    def __init__(self):
        """Initialize the service launcher.

        :returns: None

        """
        self._services = []

    @staticmethod
    def run_server(server):
        """Start and wait for a server to finish.

        :param service: Server to run and wait for.
        :returns: None

        """
        server.start()
        server.wait()

    def launch_server(self, server):
        """Load and start the given server.

        :param server: The server you would like to start.
        :returns: None

        """
        gt = eventlet.spawn(self.run_server, server)
        self._services.append(gt)

    def stop(self):
        """Stop all services which are currently running.

        :returns: None

        """
        for service in self._services:
            service.kill()

    def wait(self):
        """Waits until all services have been stopped, and then returns.

        :returns: None

        """
        for service in self._services:
            try:
                service.wait()
            except greenlet.GreenletExit:
                pass


class Service(object):
    """Service object for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    it state to the database services table."""

    def __init__(self, host, binary, manager, report_interval=None,
                 periodic_interval=None, *args, **kwargs):
        self.host = host
        self.binary = binary
        self.manager_class_name = manager
        manager_class = utils.import_class(self.manager_class_name)
        self.manager = manager_class(host=self.host, *args, **kwargs)
        self.report_interval = report_interval
        self.periodic_interval = periodic_interval
        super(Service, self).__init__(*args, **kwargs)
        self.saved_args, self.saved_kwargs = args, kwargs
        self.timers = []

    def start(self):
        LOG.audit('Starting %(topic)s on %(host)s ',
                  {'topic': self.binary, 'host': self.host})
        utils.cleanup_file_locks()
        self.manager.init_host()
        self.model_disconnected = False
        service_ref = db.service_get_by_args(self.host,
                                                 self.binary)
        if service_ref:
            self.service_id = service_ref['id']
        else:
            self._create_service_ref()

        if self.report_interval:
            pulse = utils.LoopingCall(self.report_state)
            pulse.start(interval=self.report_interval, now=False)
            self.timers.append(pulse)

        if self.periodic_interval:
            periodic = utils.LoopingCall(self.periodic_tasks)
            periodic.start(interval=self.periodic_interval, now=False)
            self.timers.append(periodic)

    def _create_service_ref(self):
        service_ref = db.service_create({'host': self.host,
                                         'binary': self.binary,
                                         'report_count': 0})
        self.service_id = service_ref['id']

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, host=None, binary=None, manager=None,
               report_interval=None, periodic_interval=None):
        """Instantiates class and passes back application object.

        :param host: defaults to hostname
        :param binary: defaults to basename of executable
        :param manager: defaults to <binary>_manager
        :param report_interval: defaults to options.report_interval
        :param periodic_interval: defaults to options.periodic_interval

        """
        if not host:
            host = socket.gethostname()
        if not binary:
            binary = os.path.basename(inspect.stack()[-1][1])
        if not manager:
            manager = getattr(options, '%s_manager' % binary, None)
        if not report_interval:
            report_interval = options.report_interval
        if not periodic_interval:
            periodic_interval = options.periodic_interval
        service_obj = cls(host, binary, manager,
                          report_interval, periodic_interval)

        return service_obj

    def kill(self):
        """Destroy the service object in the datastore."""
        self.stop()
        try:
            db.service_destroy(self.service_id)
        except exception.NotFound:
            LOG.warn('Service killed that has no database entry')

    def stop(self):
        # Try to shut the connection down, but if we get any sort of
        # errors, go ahead and ignore them.. as we're shutting down anyway
        try:
            self.conn.close()
        except Exception:
            pass
        for x in self.timers:
            try:
                x.stop()
            except Exception:
                pass
        self.timers = []

    def wait(self):
        for x in self.timers:
            try:
                x.wait()
            except Exception:
                pass

    def periodic_tasks(self, raise_on_error=options.debug):
        """Tasks to be run at a periodic interval."""
        self.manager.periodic_tasks(raise_on_error=raise_on_error)

    def report_state(self):
        """Update the state of this service in the datastore."""
        state_catalog = {}
        try:
            try:
                service_ref = db.service_get(self.service_id)
            except exception.NotFound:
                LOG.debug('The service database object disappeared, '
                            'Recreating it.')
                self._create_service_ref()
                service_ref = db.service_get(self.service_id)

            state_catalog['report_count'] = service_ref['report_count'] + 1

            db.service_update(self.service_id, state_catalog)

            if getattr(self, 'model_disconnected', False):
                self.model_disconnected = False
                LOG.error('Recovered model server connection!')

        #this should probably only catch connection errors
        except Exception:  # pylint: disable=W0702
            if not getattr(self, 'model_disconnected', False):
                self.model_disconnected = True
                LOG.exception('model server went away')

_launcher = None


def serve(*servers):
    global _launcher
    if not _launcher:
        _launcher = Launcher()
    for server in servers:
        _launcher.launch_server(server)


def wait():
    LOG.debug('Full set of options:')
    for opt in options:
        opt_get = options.as_dict().get(opt, None)
        # hide flag contents from log if contains a password
        # should use secret flag when switch over to openstack-common
        if ("password" in opt or \
            "_key" in opt or \
            opt == "sql_connection" or \
            "user" in opt or \
            "passwd" in opt):
            LOG.debug('%(opt)s : HIDDEN' % locals())
        else:
            LOG.debug('%(opt)s : %(opt_get)s' % locals())
    try:
        _launcher.wait()
    except KeyboardInterrupt:
        _launcher.stop()
