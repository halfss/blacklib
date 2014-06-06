import tornado.web

from ops import log as logging
LOG = logging.getLogger(__name__)

url_map = {
            r"/helloworld$": 'helloworld',
            r"/test2": 'test2',
        }

class helloworld(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World! I love this world!")
        LOG.debug('hello world is request')

class test2(tornado.web.RequestHandler):
    def get(self):
        self.write("test2")
        LOG.info('hello world is request')
