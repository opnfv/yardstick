import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

engine = create_engine('sqlite:////tmp/yardstick.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    subclasses = [subclass.__name__ for subclass in Base.__subclasses__()]
    logger.debug('Import models: %s', subclasses)
    Base.metadata.create_all(bind=engine)
