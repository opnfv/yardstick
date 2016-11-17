import re
import logging

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
        client = InfluxDBClient(ip, conf.PORT, username, password, db_name)
        return client
    except ConfigParser.NoOptionError as e:
        print 'can not find the key'
        raise e


def _get_ip(url):
    pattern = r'http://(.*):8086.*'
    result = re.search(pattern, url)
    return result.group(1)


def _write_data(measurement, field, timestamp, tags):
    point = {}
    point['measurement'] = measurement
    point['fields'] = field
    point['time'] = timestamp
    point['tags'] = tags

    try:
        client = get_data_db_client()

        logger.info('Start to write data:' + str(point))
        client.write_points([point])
    except RuntimeError:
        logger.info('dispatcher is not influxdb')


def write_data_tasklist(task_id, timestamp, status, error=''):
    field = {'status': status, 'error': error}
    tags = {'task_id': task_id}
    _write_data('tasklist', field, timestamp, tags)
