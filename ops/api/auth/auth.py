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
            self.endpoint = options.keystone_endpoint
            self.user = self._auth(request)
            if isinstance(self.user, tuple):
                self.set_status(self.user[1])
                self._transforms = []
                return self.finish(str(self.user[1]))
            self.context = {'user_id': self.user['users']['id'],
                            'tenant_id': self.user['users']['tenantId'],
                            'user': self.user,
                            'start': int(self.get_argument("start", 0)),
                            'length': int(self.get_argument("length", 10000))}

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()

    def _auth(self, request):
        token = request.headers.get("X-Auth-Token") or self.get_argument('token', False) 
        if not token:
            """Reject the request"""
            return (False, 400)
            #self.set_status(400)
            #self._transforms = []
            #return self.finish("Incomplete requests")
        return self._auth_by_token(token)

    def _auth_by_token(self, token):
        """
        By token Authenticate roles
        """
        backend = cache.Backend()
        user_has_roles = backend.get_user_roles(token)
        if not user_has_roles:
            Msg = self.get_usermsg_from_keystone(token)
            if isinstance(Msg, tuple):
                return Msg
            backend.set(token, Msg)
            backend.set(Msg['users']['id'], Msg)
            user_has_roles = backend.get_user_roles(token)
        if not self.method_mapping_roles(user_has_roles):
            """Reject the request"""
            return (False, 401)
            #self.set_status(401)
            #self._transforms = []
            #return self.finish("401 Authorization Required")
        return backend.get(token)

    def get_usermsg_from_keystone(self, token):
        """
        Return object from keystone by token 
        """
        try:
            headers = {'X-Auth-Token': token, 'Content-type':'application/json'}
            user_info = utils.get_http(url=options.keystone_endpoint+'/users', headers=headers) 
            role_info = utils.get_http(url=options.keystone_endpoint+'/tenants/%s/users/%s/roles' % (user_info.json()['tenantId'], user_info.json()['id']), headers=headers) 
            print role_info.json()
            return {'users': user_info.json(), 'roles': [role for role in role_info.json()['roles'] if role], 'admin': 'admin' in [role['name'] for role in role_info.json()['roles'] if role]}
        except Exception,e:
            print "Get usermsg error....\n"*3
            print e
            return (False, 401)
            #self.set_status(401)
            #self._transforms = []
            #self._finished = False
            #return self.finish("401 Authorization Required")

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
            if not allowrole.endswith("$"):
                allowrole += "$"
            if not allowrole.startswith("^"):
                allowrole = "^" + allowrole
            pattern = re.compile(allowrole)
            for role in set(user_has_roles):
                if pattern.match(role):
                    return True
        return False

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
                            'length': int(self.get_argument("length", 10000))}

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()
