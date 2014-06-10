#-*- coding:utf-8 -*-
import tornado.web
import redis
import cPickle

from keystoneclient.v2_0 import client
from ops.api.auth import policy
from ops.api.contrib import *


class BaseAuth(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(BaseAuth, self).__init__(application, request, **kwargs)
        self.endpoint = "http://127.0.0.1:35357/v2.0"
        self._auth(request)

    def _auth(self, request):
        token = request.headers.get("X-Auth-Token", None)
        if not token:
            """Reject the request"""
            self.set_status(404)
            self._transforms = []
            return self.finish("<html><body><h1>404 Not Found</h1></body></html>")
        self._auth_by_token(token)

    def _auth_by_token(self, token):
        """
        By token Authenticate roles
        """
        backend = Backend()
        user_has_roles = backend.get_user_roles(token)
        if not user_has_roles:
            user_has_roles = self.get_roles_from_keystone(token)
            backend.set_user_msg(token, self.get_usermsg_from_keystone(token))
        if not self.method_mapping_roles():
            if not filter(lambda x: x in user_has_roles, self.method_mapping_roles()):
                """Reject the request"""
                self.set_status(401)
                self._transforms = []
                return self.finish("<html><body><center><h1>401 Authorization Required</h1></center></body></html>")

    def get_usermsg_from_keystone(self, token):
        """
        Return object from keystone by token 
        """
        try:
            return client.Client(token=token, endpoint=self.endpoint)
        except:
            return None

    def get_roles_from_keystone(self, token):
        """
        Return list with roles by token
        """
        usermsg = self.get_usermsg_from_keystone(token)
        if usermsg:
            return map(lambda role: role.name, usermsg.roles.list())
        return []

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


class Backend(object):
    def __init__(self):
        cached_backend = options.cached_backend
        host, port_db = cached_backend.split('://')[1].split(':')
        port, db = port_db.split("/")
        self.conn = redis.StrictRedis(host=host, port=port, db=db)

    def get_user_msg(self, token):
        """
        Return object with token
        """
        try:
            ret = self.conn.get(token)
            if ret:
                ret = cPickle.loads(ret)["msg"]
        except:
            ret = None
        return ret

    def set_user_msg(self, token, user_msg):
        """
        Set user's token with user msg into redis-server.
        Expire 900sec or 15min
        """
        try:
            if user_msg:
                msg = cPickle.dumps({"msg": user_msg})
                self.conn.set(token, msg)
                self.conn.expire(token, 900)
                return True
        except:
            self.conn.delete(token)
            return False

    def get_user_roles(self, token):
        user_msg = self.get_user_msg(token)
        if user_msg:
            return map(lambda role: role.name, user_msg.roles.list())
        return []
