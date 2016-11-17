from pyroute2 import IPDB


# configuration for influxdb
GATEWAY_IP = IPDB().routes['default'].gateway
PORT = 8086

TEST_ACTION = ['runTestCase']

TEST_CASE_PATH = '../tests/opnfv/test_cases/'

TEST_CASE_PRE = 'opnfv_yardstick_'

TEST_SUITE_PATH = '../tests/opnfv/test_suites/'

OUTPUT_CONFIG_FILE_PATH = '/etc/yardstick/yardstick.conf'
