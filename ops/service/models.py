#codint=utf8
from sqlalchemy import Column, Integer, String
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float

from ops.db.models import BASE, OpsBase
from ops.db.session import register_models

class Service(BASE, OpsBase):
    """Represents a running service on a host."""

    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))
    binary = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)

register_models((Service,))
