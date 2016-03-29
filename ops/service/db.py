from ops.db.session import model_query, get_session
from ops import exception

from ops.service import models as service_models
from ops.db.models import *

def service_get_by_args(host, binary):
    return model_query(service_models.Service).\
                     filter_by(host=host).\
                     filter_by(binary=binary).\
                     first()

def service_create(values):
    service_ref = service_models.Service()
    service_ref.update(values)
    service_ref.save()
    return service_ref

def service_list():
    return model_query(service_models.Service).all()

def service_get(service_id, session=None):
    result = model_query(service_models.Service, session=session).\
                    filter_by(id=service_id).\
                    first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)
    return result


def service_update(service_id, values):
    session = get_session()
    with session.begin():
        service_ref = service_get(service_id, session=session)
        service_ref.update(values)
        service_ref.save(session=session)

def count_list():
    return model_query(APICount).all()

def count_insert_or_update(name, url):
    print name, url
    session = get_session()
    result = model_query(APICount, session=session).\
                    filter_by(name=name).\
                    filter_by(url=url).\
                    first()
    if not result:
        with session.begin():
            result = APICount()
            result.update({'name': name, 'url': url, 'count': 1})
            result.save()
    else:
        result.count += 1
        result.save(session=session)
    return result
