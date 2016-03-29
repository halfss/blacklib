import tornado.web

from ops import log as logging
LOG = logging.getLogger(__name__)

url_map = {
            r"/helloworld3$": 'helloworld',
        }

class helloworld(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello World! I love this world3!")
        LOG.debug('hello world is request')
