from sqlalchemy import Column, Integer, BigInteger, String, schema
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float

from ops import options
from ops.db.models import BASE
from ops.db.session import register_models

options = options.get_options()

class CostLog(BASE):
    '''
    status:
        active: the instance is in use, means it's stilling billing
        deleted: the instance is deleted; means it's already settlement
    '''
    __tablename__ = 'cost_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255))
    user_id = Column(String(255))
    cost = Column(Float, nullable=False, default=0)
    unit = Column(Float, nullable=False, default=0)
    status = Column(String(255), nullable=False, default='active')


register_models((CostLog,))
