from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from api.database import Base


class Tasks(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    task_id = Column(String(30))
    status = Column(Integer)
    error = Column(String(120))
    details = Column(String(120))

    def __repr__(self):
        return '<Task %r>' % Tasks.task_id
