#-*- coding:utf-8 -*-
import tornado.web
import redis

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
        print "============================"
        print token
        if not token:
            """Reject the request"""
            #raise tornado.web.HTTPError(404)
            print "xxxxxx111"
            return self.write("deny!!!!")
            print "xxxxxx222"
        self._auth_by_token(token)

    def _auth_by_token(self, token):
        """
        Auth
        """
        backend = Backend()
        user_has_roles = backend.get_user_roles(token)
        print "Redis:",user_has_roles
        if not user_has_roles:
            user_has_roles = self.get_roles_from_keystone(token)
            backend.set_user_roles(token, user_has_roles)
        print "Last:",user_has_roles
        print "Method:", self.method_mapping_roles()
        if not filter(lambda x: x in user_has_roles, self.method_mapping_roles()):
            """Reject the request"""
            print "deny~~~~~~~"

    def get_roles_from_keystone(self, token):
        """
        Return a list about roles by token
        ["admin", "common"]
        """
        try:
            keystone = client.Client(token=token, endpoint=self.endpoint)
            return [role.name for role in keystone.roles.list()]
        except:
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

    def get_user_roles(self, token):
        """
        Return list about token from redis-server
        """
        try:
            ret = self.conn.lrange(token, 0, -1)
        except:
            ret = []
        return ret

    def set_user_roles(self, token, roles):
        """
        Set user's token with roles into redis-server.
        Expire 900sec or 15min
        """
        try:
            if isinstance(roles, (list, tunple)):
                for role in roles:
                    self.conn.lpush(token, role)
                self.conn.expire(token, 900)
                return True
        except:
            self.conn.delete(token)
            return False
