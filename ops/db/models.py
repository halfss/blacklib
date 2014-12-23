"""
SQLAlchemy models
"""

from sqlalchemy.orm import relationship, backref, object_mapper
from sqlalchemy import Column, Integer, BigInteger, String, schema
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import ForeignKeyConstraint

from sqlalchemy.dialects.postgresql import JSON

from ops.db.session import get_session, register_models

import ops.exception
from ops.options import get_options
from ops import utils

options = get_options()

BASE = declarative_base()

class OpsBase(object):
    """Base class for Ops Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    created_at = Column(DateTime, default=utils.utcnow)
    updated_at = Column(DateTime, onupdate=utils.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    metadata = None

    def save(self, session=None):
        """Save this object."""
        if not session:
            session = get_session()
        session.add(self)
        try:
            session.flush()
        except IntegrityError, e:
            if str(e).endswith('is not unique'):
                raise exception.Duplicate(str(e))
            else:
                raise

    def delete(self, session=None):
        """Delete this object."""
        self.deleted = True
        self.deleted_at = utils.utcnow()
        self.save(session=session)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict"""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins."""
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()


class APICount(BASE, OpsBase):
    "count api caled"
    __tablename__ = 'api_count'
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    url = Column(String(1024))
    count = Column(Integer)

register_models((APICount,))
