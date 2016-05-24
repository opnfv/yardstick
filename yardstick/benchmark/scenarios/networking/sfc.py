import pkg_resources
import time
import logging
import subprocess

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)


class Sfc(base.Scenario):
    ''' SFC scenario class '''

    __scenario_type__ = "sfc"

    PRE_SETUP_SCRIPT = 'sfc_pre_setup.bash'
    TACKER_SCRIPT = 'sfc_tacker.bash'
    SERVER_SCRIPT = 'sfc_server.bash'
    TEARDOWN_SCRIPT = "sfc_teardown.bash"

    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False
        self.teardown_done = False

    def setup(self):
        '''scenario setup'''
        self.tacker_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.TACKER_SCRIPT)

        self.server_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.SERVER_SCRIPT)

        ''' calling Tacker to instantiate VNFs and Service Chains '''
        cmd_tacker = "%s" % (self.tacker_script)
        subprocess.call(cmd_tacker, shell=True)

        target = self.context_cfg['target']
        target_user = target.get('user', 'root')
        target_pwd = target.get('password', 'opnfv')
        target_ip = target.get('ip', None)

        ''' webserver start automatically during the vm boot '''
        LOG.info("user:%s, target:%s", target_user, target_ip)
        self.server = ssh.SSH(target_user, target_ip, password=target_pwd)
        self.server.wait(timeout=600)
        self.server.run("cat > ~/server.sh",
                        stdin=open(self.server_script, "rb"))
        cmd_server = "sudo bash server.sh"
        LOG.debug("Executing command: %s", cmd_server)
        status, stdout, stderr = self.server.execute(cmd_server)
        LOG.debug("Output server command: %s", status)
        #It takes a bit until the HTTP process is up
        time.sleep(7)

        self.setup_done = True

    def run(self, result):
        ''' Creating client and server VMs to perform the test'''
        host = self.context_cfg['host']
        host_user = host.get('user', 'cirros')
        host_pwd = host.get('password', 'cubswin:)')
        host_ip = host.get('ip', None)

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

        if not self.setup_done:
            self.setup()

        target = self.context_cfg['target']
        target_ip = target.get('ip', None)

        cmd_client = "curl " + target_ip
        LOG.debug("Executing command: %s", cmd_client)
        result = self.client.execute(cmd_client)
        if "WORKED" in result[1]:
            LOG.debug("HTTP WORKED!!!!")
        LOG.debug("Output client command: %s", result)
        time.sleep(2)

    def teardown(self):
        ''' for scenario teardown remove tacker VNFs, chains and classifiers'''
        self.teardown_script = pkg_resources.resource_filename(
            "yardstick.benchmark.scenarios.networking",
            Sfc.TEARDOWN_SCRIPT)
        subprocess.call(self.teardown_script, shell=True)
        self.teardown_done = True


'''def _test():

    internal test function
    logger = logging.getLogger("Sfc Yardstick")
    logger.setLevel(logging.DEBUG)

    result = {}

    sfc = Sfc()
    sfc.setup()
    sfc.run(result)
    print result
    sfc.teardown()

if __name__ == '__main__':
    _test()'''
