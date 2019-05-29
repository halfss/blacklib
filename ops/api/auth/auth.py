#-*- coding:utf-8 -*-
import os
import re
import imp
import redis
import cPickle
import tornado.web

from ops.options import get_options
from ops import cache
from ops import utils
from ops import log as logging

from ops.service import db as service_db

auth_opts = [
        {
            "name": "policy",
            "default": "ops.api.auth.policy",
            "help": "",
            "type": str,
        },
]

options = get_options(auth_opts, 'auth')
LOG = logging.getLogger()

def load_policy():
    option_split = options.policy.split(".")
    mod = option_split[0]
    fun = options.policy[options.policy.rfind('.')+1:]
    fn_, modpath, desc = imp.find_module(mod)
    fn_, path, desc = imp.find_module(fun, [os.path.join(modpath, "/".join(option_split[1:-1]))])
    return imp.load_module(fun, fn_, path, desc)

class BaseAuth(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseAuth, self).__init__(application, request, **kwargs)
        if request.method != 'OPTIONS':
            self.policy = load_policy()
            self.token = request.headers.get("X-Auth-Token") or self.get_argument('token', False)
            authed, self.user = self._auth(request)
            print authed
            if authed and self.user:
                self.context = {'start': int(self.get_argument("start", 0)),
                                'length': int(self.get_argument("length", 10000))}
                self.context['user'] = self.user
                LOG.debug("auth token:%s by %s" % (self.token, self.context))
            else:
                self.return_401()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()

    def _auth(self, request):
        if not self.token:
            """Reject the request"""
            return False, {}
        return self._auth_by_token(self.token)

    def _auth_by_token(self, token):
        """
        By token Authenticate roles
        """
        backend = cache.Backend()
        user_info = backend.get(self.token)
        print 1, user_info
        if not user_info:
            authed, Msg = self.get_usermsg_from_keystone(self.token)
            print  authed, Msg
            if authed:
                backend.set(self.token, Msg)
                return True, backend.get(self.token)
            else:
                return False, {}
        else:
            return True, user_info

    def get_usermsg_from_keystone(self, token):
        """
        Return object from keystone by token
        """
        try:
            headers = {'X-Auth-Token': token, 'Content-type':'application/json'}
            user_info = utils.get_http(url=options.auth_endpoint, headers=headers)
            return True, user_info.json()['result']
        except Exception,e:
            return False, {}

    def method_mapping_roles(self, user_has_roles):
        """
        Return list about request handler mapping roles
        """
        httpmethod = self.request.method
        httpuri = self.request.path
        target_policy = {}
        if not hasattr(self.policy, "policy"):
            return False

        if not isinstance(self.policy.policy, dict):
            return False

        default_policy = {}
        if hasattr(self.policy, "default"):
            default_policy = self.policy.default
            if not isinstance(default_policy, dict):
                default_policy = {}

        for k,v in self.policy.policy.iteritems():
            pattern = re.compile(k)
            if pattern.match(httpuri):
                target_policy = v
                break

        allowroles = [str(i) for i in target_policy.get(httpmethod, []) + default_policy.get(httpmethod, []) if i]
        for allowrole in set(allowroles):
            pattern = re.compile(allowrole)
            for role in set(user_has_roles):
                if pattern.match(role):
                    return True
        return False

    def return_401(self):
        self.clear()
        self._transforms = []
        self.set_status(401)
        return self.finish("401 Authorization Required")

    def on_finish(self):
        if self.request.method != 'OPTIONS':
            try:
                user = self.user['users']['name']
            except:
                user = None
            if user:
                service_db.count_insert_or_update(user, self.request.uri)


class Base(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(Base, self).__init__(application, request, **kwargs)
        if request.method != 'OPTIONS':
            self.context = {'start': int(self.get_argument("start", 0)),
                            'length': int(self.get_argument("length", 200))}

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()
