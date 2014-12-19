#-*- coding:utf-8 -*-
import tornado.web
import imp
import redis
import cPickle

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

try:
    mod = options.policy[:options.policy.rfind('.')]
    fun = options.policy[options.policy.rfind('.')+:]
    fn_, path, desc = imp.find_module(mod)
    _mod = imp.load_module(mod, fn_, path, desc)
    policy = getattr(mod, fun)
except Exception,e:
    return e
    

class BaseAuth(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseAuth, self).__init__(application, request, **kwargs)
        if request.method != 'OPTIONS':
            self.endpoint = options.keystone_endpoint
            self.user = self._auth(request)
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
        token = request.headers.get("X-Auth-Token", None)
        if not token:
            """Reject the request"""
            self.set_status(400)
            self._transforms = []
            return self.finish("Incomplete requests")
        return self._auth_by_token(token)

    def _auth_by_token(self, token):
        """
        By token Authenticate roles
        """
        backend = cache.Backend()
        user_has_roles = backend.get_user_roles(token)
        if not user_has_roles:
            backend.set(token, self.get_usermsg_from_keystone(token))
            user_has_roles = backend.get_user_roles(token)
        if not self.method_mapping_roles(user_has_roles):
            """Reject the request"""
            self.set_status(401)
            self._transforms = []
            return self.finish("401 Authorization Required")
        return backend.get(token)

    def get_usermsg_from_keystone(self, token):
        """
        Return object from keystone by token 
        """
        try:
            headers = {'X-Auth-Token': token, 'Content-type':'application/json'}
            user_info = utils.get_http(url=options.keystone_endpoint+'/users', headers=headers) 
            role_info = utils.get_http(url=options.keystone_endpoint+'/tenants/%s/users/%s/roles' % (user_info.json()['tenantId'], user_info.json()['id']), headers=headers) 
            return {'users': user_info.json(), 'roles': role_info.json()['roles'], 'admin': 'admin' in [role['name'] for role in role_info.json()['roles']]}
        except:
            self.set_status(401)
            self._transforms = []
            self._finished = False
            return self.finish("401 Authorization Required")

    def method_mapping_roles(self, user_has_roles):
        """
        Return list about request handler mapping roles
        """
        httpmethod = self.request.method
        httpuri = self.request.path
        target_policy = {}
        if not policy.hasattr("policy"):
            return False

        default_policy = {}
        if policy.hasattr("default"):
            default_policy = policy.default
            if not isinstance(default_policy, dict):
                default_policy = {}

        for k,v in policy.policy.iteritems():
            pattern = re.compile(k)
            if pattern.match(httpuri):
                target_policy = v
                break

        allowroles = target_policy.get(httpmethod, []) + default_policy.get(httpmethod, [])
        for allowrole in set(allowroles):
            if not endswith("$"):
                allowrole += "$"
            if not startswith("^"):
                allowrole = "^" + allowrole
            pattern = re.compile(allowrole)
            for role in set(user_has_roles):
                if pattern.match(role):
                    return True
        return False

    def on_finish(self):
        if self.request.method != 'OPTIONS':
            service_db.count_insert_or_update(self.user['users']['name'], self.request.uri)


class Base(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(Base, self).__init__(application, request, **kwargs)

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()
