#-*- coding:utf-8 -*-
import tornado.web
import redis
import cPickle

from ops.options import get_options
from ops.api.auth import policy
from ops import cache
from ops import utils

auth_opts = [
    {
        "name": 'keystone_endpoint',
        "default": 'http://127.0.0.1:35357/v2.0',
        "help": 'the keystone endpoint url',
        "type": str,
    }]

options = get_options(auth_opts, 'auth')

class BaseAuth(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseAuth, self).__init__(application, request, **kwargs)
        if request.method != 'OPTIONS':
            self.endpoint = options.keystone_endpoint
            self.user = self._auth(request)
            self.start, self.length = self.get_start_and_length()

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
        if self.method_mapping_roles():
            if not filter(lambda x: x in user_has_roles, self.method_mapping_roles()):
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

    def method_mapping_roles(self):
        """
        Return list about request handler mapping roles
        """
        import inspect,os,sys
        current_method_path = inspect.getfile(self.__class__)
        current_method_list = os.path.splitext(current_method_path)[0].split("/api/")[1].split('/')
        current_method_list.append(self.__class__.__name__)
        current_method = '.'.join(current_method_list)
        return policy.policy.get(current_method, [])

    def get_start_and_length(self):
        start = self.get_argument("start", 0)
        length = self.get_argument("length", 100)
        if start:
            if not length:
                self.set_status(400)
                return (0,100)
            try:
                start = int(start)
                length = int(length)
                return (start, length)
            except:
                return (0, 100)
        else:
            return (0, 100)

class Base(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(Base, self).__init__(application, request, **kwargs)
        self.start, self.length = self.get_start_and_length()

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE")
        self.set_header("Access-Control-Allow-Headers", "X-Auth-Token, Content-type")
        self.set_header("Content-Type", "application/json")

    def options(self, *args, **kwargs):
        self.finish()

    def get_start_and_length(self):
        start = self.get_argument("start", 0)
        length = self.get_argument("length", 100)
        if start:
            if not length:
                self.set_status(400)
                return (0,100)
            try:
                start = int(start)
                length = int(length)
                return (start, length)
            except:
                return (0, 100)
        else:
            return (0, 100)
