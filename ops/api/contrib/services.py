import tornado.web
import json

from ops.db.session import query_result_json

from ops.service import db
from ops import log as logging





LOG = logging.getLogger(__name__)

url_map = {
            r"/service$": 'service_list',
        }

class service_list(tornado.web.RequestHandler):
    def get(self):
        services = query_result_json(db.service_list())
        self.write(services)
        LOG.debug('hello world is request')
