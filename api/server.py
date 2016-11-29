##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging

from flask import Flask
from flask_restful import Api

from api.urls import urlpatterns
from yardstick import _init_logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

api = Api(app)

reduce(lambda a, b: a.add_resource(b.resource, b.url,
                                   endpoint=b.endpoint) or a, urlpatterns, api)

if __name__ == '__main__':
    _init_logging()
    logger.info('Starting server')
    app.run(host='0.0.0.0')
