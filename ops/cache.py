#-*- coding:utf-8 -*-
import redis
import cPickle

from ops.options import get_options


auth_opts = [
    {
        "name": "cached_backend",
        "default": 'redis://127.0.0.1:6379/0',
        "help": 'cached backend uri',
        "type": str,
    },
    {
        "name": 'cache_timeout',
        "default": '3600',
        "help": 'cache timeout seconds',
        "type": str,
    }]

options = get_options(auth_opts, 'cache')

class Backend(object):
    def __init__(self):
        cached_backend = options.cached_backend
        host, port_db = cached_backend.split('://')[1].split(':')
        port, db = port_db.split("/")
        self.conn = redis.StrictRedis(host=host, port=port, db=db)

    def get(self, id, default=None):
        """
        Return object with id 
        """
        try:
            ret = self.conn.get(id)
            if ret:
                ret = cPickle.loads(ret)["msg"]
        except:
            ret = default
        return ret

    def set(self, id, user_msg, timeout=options.cache_timeout):
        """
        Set obj into redis-server.
        Expire 3600 sec
        """
        try:
            if user_msg:
                msg = cPickle.dumps({"msg": user_msg})
                self.conn.set(id, msg)
                self.conn.expire(id, timeout)
                return True
        except:
            self.conn.delete(id)
            return False

    def delete(self, id):
        try:
            self.conn.delete(id)
        except:
            pass

    def get_user_roles(self, id):
        cache_id = '%s_%s' % ('roles', id)
        if not self.get(id):
            return []
        roles = self.get(cache_id)
        if not roles:
            roles = [role['name'] for role in self.get(id)['roles']]
            self.set(cache_id, roles)
        return roles
