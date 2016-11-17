import subprocess


cmd = "route | grep default | awk '{print $2}'"
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
output = p.communicate()[0]

# configuration for influxdb
GATEWAY_IP = output.splitlines()[0]
PORT = 8086

TEST_ACTION = ['runTestCase']

TEST_CASE_PATH = '../tests/opnfv/test_cases/opnfv_yardstick_'

TEST_SUITE_PATH = '../tests/opnfv/test_suites/'

OUTPUT_CONFIG_FILE_PATH = '/etc/yardstick/yardstick.conf'
