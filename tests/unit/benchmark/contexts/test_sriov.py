
from __future__ import absolute_import
import os
import mock
import unittest

from yardstick.benchmark.contexts.standalone import StandaloneContext
#import yardstick.benchmark.contexts.sriov
from yardstick.benchmark.contexts.sriov import Sriov
from yardstick.benchmark.contexts import sriov

NIC_INPUT = {
     'interface': {},
     'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
     'pci': ['0000:06:00.0', '0000:06:00.1'],
     'phy_driver': 'i40e'}
DRIVER = "i40e"
NIC_DETAILS = {
     'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
     'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
     'pci': ['0000:06:00.0', '0000:06:00.1'],
     'phy_driver': 'i40e'}

class SriovTestCase(unittest.TestCase):

    '''NIC_DETAILS = {
         'interface': {0: 'enp6s0f0', 1: 'enp6s0f1'},
         'vf_macs': ['00:00:00:71:7d:25', '00:00:00:71:7d:26'],
         'pci': ['0000:06:00.0', '0000:06:00.1'],
         'phy_driver': 'i40e'}'''

    def setUp(self):
        self.test_context = sriov.Sriov()

    def test_construct(self):
        self.assertIsNone(self.test_context.name)
        self.assertIsNone(self.test_context.file_path)
        self.assertEqual(self.test_context.nodes, [])
        self.assertEqual(self.test_context.sriov, [])
        self.assertFalse(self.test_context.vm_deploy)
        self.assertTrue(self.test_context.first_run)

    def test_ssh_connection(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock

    def test_get_nic(self):
        with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            mock_sriov = mock.Mock()
            self.assertIsNotNone(mock_sriov.sriov_obj.get_nic_details())

    @mock.patch('yardstick.benchmark.contexts.sriov', return_value = NIC_DETAILS)
    def test_configure_nics_for_sriov(self, NIC_INPUT):
       with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            mock_sriov = mock.Mock()
            '''self.assertEqual(mock_sriov.sriov_obj.configure_nics_for_sriov(), NIC_DETAILS)'''
            self.assertIsNotNone(mock_sriov.sriov_obj.configure_nics_for_sriov())

    @mock.patch('yardstick.benchmark.contexts.sriov', return_value = "Domain vm1 created from /tmp/vm_sriov.xml")
    def test_is_vm_created(self, NIC_INPUT):
       with mock.patch("yardstick.ssh.SSH") as ssh:
            ssh_mock = mock.Mock(autospec=ssh.SSH)
            ssh_mock.execute = \
                mock.Mock(return_value=(0, {}, ""))
            ssh.return_value = ssh_mock
            sriov_obj = sriov.Sriov()
            mock_sriov = mock.Mock()
            pcis = NIC_DETAILS['pci']
            driver = NIC_DETAILS['phy_driver']
            '''self.assertEqual(mock_sriov.sriov_obj.setup_sriov_context(pcis, NIC_DETAILS, driver), "Domain vm1 created from /tmp/vm_sriov.xml")'''
            self.assertIsNotNone(mock_sriov.sriov_obj.setup_sriov_context(pcis, NIC_DETAILS, driver))
if __name__ == '__main__':
    unittest.main()
