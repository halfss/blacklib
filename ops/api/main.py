#coding=utf8

import tornado.httpserver
import tornado.ioloop
import tornado.web

from ops import log as logging
from ops.api.contrib import *

application = tornado.web.Application(url_map)


if __name__ == "__main__":
    LOG = logging.getLogger('api')
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()
