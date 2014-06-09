#coding=utf8

import tornado.httpserver
import tornado.ioloop
import tornado.web

from ops import log as logging
from ops.options import get_options
from ops.api.contrib import *

options = get_options()
application = tornado.web.Application(url_map)


if __name__ == "__main__":
    LOG = logging.getLogger('api')
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.api_port)
    tornado.ioloop.IOLoop.instance().start()
