import os

DOCKER_URL = 'unix://var/run/docker.sock'

# database config
USER = 'root'
PASSWORD = 'root'
DATABASE = 'yardstick'

dirname = os.path.dirname
abspath = os.path.abspath
sep = os.path.sep

INSTALLERS = ['apex', 'compass', 'fuel', 'joid']

YARDSTICK_ROOT_PATH = dirname(dirname(dirname(abspath(__file__)))) + sep

YARDSTICK_CONFIG_DIR = '/etc/yardstick/'

YARDSTICK_CONFIG_FILE = YARDSTICK_CONFIG_DIR + 'config.yaml'

RELENG_DIR = '/home/opnfv/repos/releng'

OS_FETCH_SCRIPT = 'utils/fetch_os_creds.sh'

LOAD_IMAGES_SCRIPT = 'tests/ci/load_images.sh'

OPENSTACK_RC_FILE = YARDSTICK_CONFIG_DIR + 'openstack.creds'
