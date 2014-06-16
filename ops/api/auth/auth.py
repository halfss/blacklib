#-*- coding:utf-8 -*-
import tornado.web
import redis
import cPickle

from keystoneclient.v2_0 import client
from keystoneclient import exceptions as keystone_exceptions

from ops.options import get_options
from ops.api.auth import policy
from ops import cache

from ops.api.contrib import *


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
        self.endpoint = options.keystone_endpoint
        self._auth(request)

    def _auth(self, request):
        token = request.headers.get("X-Auth-Token", None)
        if not token:
            """Reject the request"""
            self.set_status(400)
            self._transforms = []
            return self.finish("Incomplete requests")
        self._auth_by_token(token)

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

    def get_usermsg_from_keystone(self, token):
        """
        Return object from keystone by token 
        """
        try:
            user_info = client.Client(token=token, endpoint=self.endpoint)
            user_info.roles.list()
            return user_info
        except keystone_exceptions.Unauthorized:
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
