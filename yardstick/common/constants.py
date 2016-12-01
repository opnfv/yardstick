import os

DOCKER_URL = 'unix://var/run/docker.sock'

# database config
USER = 'root'
PASSWORD = 'root'
DATABASE = 'yardstick'

INFLUXDB_IMAGE = 'tutum/influxdb'
INFLUXDB_TAG = '0.13'

GRAFANA_IMAGE = 'grafana/grafana'
GRAFANA_TAGS = '3.1.1'

dirname = os.path.dirname
abspath = os.path.abspath
sep = os.path.sep

INSTALLERS = ['apex', 'compass', 'fuel', 'joid']

YARDSTICK_ROOT_PATH = dirname(dirname(dirname(abspath(__file__)))) + sep

YARDSTICK_REPOS_DIR = '/home/opnfv/repos/yardstick'

YARDSTICK_CONFIG_DIR = '/etc/yardstick/'

YARDSTICK_CONFIG_FILE = os.path.join(YARDSTICK_CONFIG_DIR, 'config.yaml')

RELENG_DIR = '/home/opnfv/repos/releng'

OS_FETCH_SCRIPT = 'utils/fetch_os_creds.sh'

LOAD_IMAGES_SCRIPT = 'tests/ci/load_images.sh'

OPENSTACK_RC_FILE = os.path.join(YARDSTICK_CONFIG_DIR, 'openstack.creds')

YARDSTICK_ENV_ACTION_API = 'http://localhost:5000/yardstick/env/action'
