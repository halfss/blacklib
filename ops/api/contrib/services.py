import tornado.web
import json



from ops.api.auth import auth
from ops.service import db
from ops import log as logging

from ops.db.session import query_result_json

LOG = logging.getLogger(__name__)
url_map = {
            r"/service$": 'service',
        }

class service(auth.BaseAuth):
    def get(self):
        services = query_result_json(db.service_list())
        self.write(services)
