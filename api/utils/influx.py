import logging
from urlparse import urlsplit

from influxdb import InfluxDBClient
import ConfigParser

from api import conf

logger = logging.getLogger(__name__)


def get_data_db_client():
    parser = ConfigParser.ConfigParser()
    try:
        parser.read(conf.OUTPUT_CONFIG_FILE_PATH)
        dispatcher = parser.get('DEFAULT', 'dispatcher')

        if 'influxdb' != dispatcher:
            raise RuntimeError

        ip = _get_ip(parser.get('dispatcher_influxdb', 'target'))
        username = parser.get('dispatcher_influxdb', 'username')
        password = parser.get('dispatcher_influxdb', 'password')
        db_name = parser.get('dispatcher_influxdb', 'db_name')
        return InfluxDBClient(ip, conf.PORT, username, password, db_name)
    except ConfigParser.NoOptionError:
        logger.error('can not find the key')
        raise


def _get_ip(url):
    return urlsplit(url).netloc.split(':')[0]


def _write_data(measurement, field, timestamp, tags):
    point = {
        'measurement': measurement,
        'fields': field,
        'time': timestamp,
        'tags': tags
    }

    try:
        client = get_data_db_client()

        logger.debug('Start to write data: %s', point)
        client.write_points([point])
    except RuntimeError:
        logger.debug('dispatcher is not influxdb')


def write_data_tasklist(task_id, timestamp, status, error=''):
    field = {'status': status, 'error': error}
    tags = {'task_id': task_id}
    _write_data('tasklist', field, timestamp, tags)
