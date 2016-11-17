import logging

from flask import Flask
from flask_restful import Api

from api.urls import urlpatterns

logger = logging.getLogger(__name__)

app = Flask(__name__)

api = Api(app)

reduce(lambda a, b: a.add_resource(b.resource, b.url,
                                   endpoint=b.endpoint) or a, urlpatterns, api)

if __name__ == '__main__':
    logger.info('Starting server')
    app.run(host='0.0.0.0', port=7777)
