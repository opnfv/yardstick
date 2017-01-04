##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
from itertools import ifilter

from flask import Flask
from flask_restful import Api
from flasgger import Swagger

from api.database import Base
from api.database import engine
from api.database import db_session
from api.database import models
from api.urls import urlpatterns
from yardstick import _init_logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

Swagger(app)

api = Api(app)


@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


def init_db():
    def func(a):
        try:
            if issubclass(a, Base):
                return True
        except TypeError:
            pass
        return False

    subclasses = [a for a in ifilter(func, models.__dict__.values())]
    logger.debug('Import models: %s', subclasses)
    Base.metadata.create_all(bind=engine)


init_db()
reduce(lambda a, b: a.add_resource(b.resource, b.url,
                                   endpoint=b.endpoint) or a, urlpatterns, api)

if __name__ == '__main__':
    _init_logging()
    logger.setLevel(logging.DEBUG)
    logger.info('Starting server')
    app.run(host='0.0.0.0')
