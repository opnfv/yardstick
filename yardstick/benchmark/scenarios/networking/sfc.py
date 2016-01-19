import pkg_resources
import logging
import subprocess

import yardstick.ssh as ssh
from yardstick.benchmark.scenarios import base

LOG = logging.getLogger(__name__)

class Sfc(base.Scenario):

    __scenario_type__ = "Sfc"

    PRE_SETUP_SCRIPT = 'sfc_pre_setup.bash'
    TACKER_SCRIPT = 'sfc_tacker.bash'
    SERVER_SCRIPT = 'sfc_server.bash'


    def __init__(self, scenario_cfg, context_cfg):
        self.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg
        self.setup_done = False

    def setup(self):
        '''scenario setup'''
        self.pre_setup_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.PRE_SETUP_SCRIPT)

        self.tacker_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.TACKER_SCRIPT)

        self.server_script = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.SERVER_SCRIPT)


        ''' creating flavor and uploading sfc image'''
        cmd_pre = "%s" % (self.pre_setup_script)
        subprocess.call(cmd_pre, shell=True)

        ''' calling Tacker to instantiate VNFs and Service Chains '''
        cmd_tacker = "%s" % (self.tacker_script)
        subprocess.call(cmd_tacker, shell=True)

        self.setup_done = True

    def run(self):
        ''' Creating client and server VMs to perform the test '''
        host = self.context_cfg['host']
        host_user = host.get('user', 'cirros')
        host_pwd = host.get('password', 'cubswin:)')
        host_ip = host.get('ip', None)

        target = self.context_cfg['target']
        target_user = target.get('user', 'root')
        target_pwd = target.pwd('password', 'octopus')
        target_ip = target.get('ip', None)

        # webserver start automatically during the vm boot
        LOG.info("user:%s, target:%s", target_user, target_ip)
        self.server = ssh.SSH(target_user, target_ip, password=target_pwd)
        self.server.wait(timeout=600)
        self.server.run("cat > ~/server.sh",
                        stdin=open(self.server_script, "rb"))
        cmd_server = "sudo bash server.sh"
        status, stdout, stderr = self.server.execute(cmd_server)

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

        if not self.setup_done:
            self.setup()

        cmd_client = "curl %s", target_ip
        self.client.execute(cmd_client)

def _test():
    '''internal test function'''
    logger = logging.getLogger("Sfc Yardstick")
    logger.setLevel(logging.DEBUG)

    sfc = Sfc()
    sfc.setup()
    sfc.run()
    pass

if __name__ == '__main__':
    _test()