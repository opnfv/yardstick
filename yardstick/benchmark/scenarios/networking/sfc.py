import pkg_resources
import time
import logging
import subprocess
import sfc_openstack
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
    TACKER_CHANGECLASSI = "sfc_change_classi.bash"

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

        ips = sfc_openstack.get_an_IP()

        target = self.context_cfg['target']
        SF1_user = target.get('user', 'root')
        SF1_pwd = target.get('password', 'opnfv')
        SF1_ip = ips[0]

        LOG.info("user:%s, host:%s", SF1_user, SF1_ip)
        self.server = ssh.SSH(SF1_user, SF1_ip, password=SF1_pwd)
        self.server.wait(timeout=600)
        cmd_SF1 = "nohup python vxlan_tool.py -i eth0 -d forward -v off -b 80 &"
        LOG.debug("Starting HTTP firewall in SF1")
        status, stdout, stderr = self.server.execute(cmd_SF1)
        result = self.server.execute("ps lax | grep python")
        if "vxlan_tool.py" in result[1]:
            LOG.debug("HTTP firewall started")

        SF2_user = target.get('user', 'root')
        SF2_pwd = target.get('password', 'opnfv')
        SF2_ip = ips[1]

        LOG.info("user:%s, host:%s", SF2_user, SF2_ip)
        self.server = ssh.SSH(SF2_user, SF2_ip, password=SF2_pwd)
        self.server.wait(timeout=600)
        cmd_SF2 = "nohup python vxlan_tool.py -i eth0 -d forward -v off -b 22 &"
        LOG.debug("Starting SSH firewall in SF2")
        status, stdout, stderr = self.server.execute(cmd_SF2)

        result = self.server.execute("ps lax | grep python")
        if "vxlan_tool.py" in result[1]:
            LOG.debug("SSH firewall started")

        self.setup_done = True

    def run(self, result):
        ''' Creating client and server VMs to perform the test'''
        host = self.context_cfg['host']
        host_user = host.get('user', 'root')
        host_pwd = host.get('password', 'opnfv')
        host_ip = host.get('ip', None)

        LOG.info("user:%s, host:%s", host_user, host_ip)
        self.client = ssh.SSH(host_user, host_ip, password=host_pwd)
        self.client.wait(timeout=600)

        if not self.setup_done:
            self.setup()

        target = self.context_cfg['target']
        target_ip = target.get('ip', None)

        cmd_client = "nc -w 5 -zv "+ target_ip +" 22"
        result = self.client.execute(cmd_client)
        
        i = 0
        if "timed out" in result[2]:
            LOG.info('\033[92m' + "TEST 1 [PASSED] ==> SSH BLOCKED" + '\033[0m')
            i = i + 1
        else:
            LOG.debug('\033[91m' + "TEST 1 [FAILED] ==> SSH NOT BLOCKED" + '\033[0m')
            return

        cmd_client = "nc -w 5 -zv "+ target_ip +" 80"
        LOG.info("Executing command: %s", cmd_client)
        result = self.client.execute(cmd_client)
        if "succeeded" in result[2]:
            LOG.info('\033[92m' + "TEST 2 [PASSED] ==> HTTP WORKS" + '\033[0m')
            i = i + 1
        else:
            LOG.debug('\033[91m' + "TEST 2 [FAILED] ==> HTTP BLOCKED" + '\033[0m')
            return

        self.tacker_classi = pkg_resources.resource_filename(
            'yardstick.benchmark.scenarios.networking',
            Sfc.TACKER_CHANGECLASSI)

        ''' calling Tacker to change the classifier '''
        cmd_tacker = "%s" % (self.tacker_classi)
        subprocess.call(cmd_tacker, shell=True)

        cmd_client = "nc -w 5 -zv "+ target_ip +" 80"
        LOG.info("Executing command: %s", cmd_client)
        result = self.client.execute(cmd_client)
        LOG.info("Output client command: %s", result)
        if "timed out" in result[2]:
             LOG.info('\033[92m' + "TEST 3 [WORKS] ==> HTTP BLOCKED" + '\033[0m')
             i = i + 1
        else:
             LOG.debug('\033[91m' + "TEST 3 [FAILED] ==> HTTP NOT BLOCKED" + '\033[0m')
             return

        cmd_client = "nc -zv "+ target_ip +" 22"
        result = self.client.execute(cmd_client + " \r")
        LOG.debug(result)

        if "succeeded" in result[2]:
             LOG.info('\033[92m' + "TEST 4 [WORKS] ==> SSH WORKS" + '\033[0m')
             i = i + 1
        else:
             LOG.debug('\033[91m' + "TEST 4 [FAILED] ==> SSH BLOCKED" + '\033[0m')
             return

        if i == 4:
             for x in range(0, 5):
                 LOG.info('\033[92m' + "SFC TEST WORKED :) \n" + '\033[0m')


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

    sfc = Sfc(scenario_cfg, context_cfg)
    sfc.setup()
    sfc.run(result)
    print result
    sfc.teardown()

if __name__ == '__main__':
    _test()'''
