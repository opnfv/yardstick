import logging

from docker import Client

from yardstick.common import constants as conf
from api.utils import common as common_utils
from api.utils import influx

logger = logging.getLogger(__name__)


def createInfluxDBContainer(args):
    try:
        container = _create_influxdb_container()
        _config_influxdb()
        return common_utils.result_handler('success', container)
    except Exception as e:
        message = 'Failed to create influxdb container: %s' % e
        return common_utils.error_handler(message)


def _create_influxdb_container():
    client = Client(base_url=conf.DOCKER_URL)

    ports = [8083, 8086]
    port_bindings = {k: k for k in ports}
    host_config = client.create_host_config(port_bindings=port_bindings)

    container = client.create_container(image='tutum/influxdb',
                                        ports=ports,
                                        command='/bin/bash',
                                        detach=True,
                                        tty=True,
                                        host_config=host_config)
    client.restart(container)
    return container


def _config_influxdb():
    client = influx.get_data_db_client()
    client.create_user(conf.USER, conf.PASSWORD, conf.DATABASE)
    client.create_database(conf.DATABASE)
