#############################################################################
# Copyright (c) 2017 Intel and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import mock
import os
import unittest

from yardstick.common.cpu_model import CpuList
from yardstick.common.cpu_model import _mask_to_set
from yardstick.common.cpu_model import CpuModel
from yardstick.common.cpu_model import CpuInfoDict
from yardstick.common.cpu_model import CpuInfo
from yardstick.common.cpu_model import CpuModelNotInPoolException
from yardstick.common.cpu_model import CpuModelWrongArgument
from yardstick import ssh


EXAMPLE_LSCPU_OUTPUT = """
Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                56
On-line CPU(s) list:   0-55
Thread(s) per core:    2
Core(s) per socket:    14
Socket(s):             2
NUMA node(s):          2
Vendor ID:             GenuineIntel
CPU family:            6
Model:                 79
Model name:            Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
Stepping:              1
CPU MHz:               1201.025
CPU max MHz:           3300.0000
CPU min MHz:           1200.0000
BogoMIPS:              4788.96
Virtualization:        VT-x
L1d cache:             32K
L1i cache:             32K
L2 cache:              256K
L3 cache:              35840K
NUMA node0 CPU(s):     0-13,28-41
NUMA node1 CPU(s):     14-27,42-55
Flags:                 fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 \
clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc \
arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor \
ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt \
tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 \
intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep \
bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total \
cqm_mbm_local dtherm ida arat pln pts
"""

EXAMPLE_PROC_CPUINFO_FILE = "example_proc_cpuinfo.txt"

EXAMPLE_KERNEL_CMDLINE = "BOOT_IMAGE=/vmlinuz-4.11.8-300.fc26.x86_64 root=/dev/mapper/fedora-root \
ro rd.lvm.lv=fedora/root rd.lvm.lv=fedora/swap rhgb quiet LANG=en_US.UTF-8 isolcpus=2,3,4,5-10,12"

EXAMPLE_KERNEL_CMDLINE_NO_ISOLCPUS = "BOOT_IMAGE=/vmlinuz-4.11.8-300.fc26.x86_64 \
root=/dev/mapper/fedora-root ro rd.lvm.lv=fedora/root rd.lvm.lv=fedora/swap rhgb \
quiet LANG=en_US.UTF-8"

EXAMPLE_HT_TOPO = """\
0: 0, 4
1: 1, 5
2: 2, 6
3: 3, 7
4: 0, 4
5: 1, 5
"""

class TestCpuList(unittest.TestCase):

    def test__init__(self):
        test_data = [
            ([], set([])),
            (None, set()),
            ('', set()),
            ('0,1,2', {0, 1, 2}),
            ([0, 1, 3], {0, 1, 3}),
            ({0, 1, 4}, {0, 1, 4}),
            ('0, 1, 2-9', {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}),
            ('0,1-5,8', {0, 1, 2, 3, 4, 5, 8}),
            (20, {2, 4}),
            (4, {2}),
            ('0b100', {2}),
            (32800, {5, 15}),
            ('0b1000000000001000', {3, 15}),
            ('0x14', {2, 4}),
        ]

        for cpus, expected in test_data:
            cpulist = CpuList(cpus)
            self.assertEqual(cpulist, expected)

        with self.assertRaises(TypeError):
            CpuList('wrong input')

    def test_ranges(self):
        examples = [
            ([1, 2, 3, 4, 5, 10, 15], '1-5,10,15'),
            ([1, 10, 11, 12, 13, 15, 18, 19, 20], '1,10-13,15,18-20'),
            ([1], '1'),
            ([], ''),
            ([1, 2, 3, 4], '1-4')
        ]
        for l, res in examples:
            self.assertEqual(str(CpuList(l)), res)

    def test_mask_to_set(self):
        examples = [
            (7, {0, 1, 2}),
            (20, {2, 4}),
            (0, set()),
            (1, {0}),
        ]
        for value, expected in examples:
            self.assertEqual(_mask_to_set(value), expected)


class TestCpuDict(unittest.TestCase):
    def test_parse(self):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        cpuinfo_path = os.path.join(curr_path, 'example_prox_cpuinfo.txt')
        with open(cpuinfo_path, 'r') as stream:
            cpuinfo_string = stream.read()
        cpuinfo = CpuInfoDict(cpuinfo_string)
        self.assertEqual(cpuinfo.cpu_list[0]['siblings'], '28')
        self.assertEqual(cpuinfo.cpu_list[0]['cpu cores'], '14')


class TestCpuInfo(unittest.TestCase):
    def setUp(self):
        connection = mock.Mock()
        self.cpuinfo = CpuInfo(connection)

    def test_cpuinfo(self):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        cpuinfo_path = os.path.join(curr_path, 'example_prox_cpuinfo.txt')
        with open(cpuinfo_path, 'r') as stream:
            cpuinfo_string = stream.read()

        def my_get_file_obj(_, my_cpuinfo): # pylint: disable=unused-argument
            my_cpuinfo.write(bytes(cpuinfo_string.encode('utf-8')))

        old_get_file_obj = self.cpuinfo.connection.get_file_obj
        try:
            self.cpuinfo.connection.get_file_obj = my_get_file_obj
            self.cpuinfo.cpuinfo # pylint: disable=pointless-statement
        finally:
            self.cpuinfo.connection.get_file_obj = old_get_file_obj

    def test_lscpu(self):
        self.cpuinfo.connection.execute = mock.Mock(return_value=(0, EXAMPLE_LSCPU_OUTPUT, ''))
        lscpu = self.cpuinfo.lscpu
        self.assertEqual(lscpu['CPU(s)'], '56')

    def test_isolcpus(self):
        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(-1, '', '')
        )
        with self.assertRaises(ssh.SSHCommandError):
            self.cpuinfo.isolcpus # pylint: disable=pointless-statement

        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(0, EXAMPLE_KERNEL_CMDLINE, '')
        )
        self.assertEqual(self.cpuinfo.isolcpus, '2,3,4,5-10,12')

        # verify memoization
        self.cpuinfo.connection.execute.reset_mock()
        self.cpuinfo.isolcpus # pylint: disable=pointless-statement
        self.cpuinfo.connection.execute.assert_not_called()

    def test_isolcpus_notset(self):
        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(0, EXAMPLE_KERNEL_CMDLINE_NO_ISOLCPUS, '')
        )
        isolcpus = self.cpuinfo.isolcpus
        self.assertIsNone(isolcpus)

    def test_numa_node_to_cpus(self):
        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(0, EXAMPLE_LSCPU_OUTPUT, ''))
        cpus = self.cpuinfo.numa_node_to_cpus(0)
        self.assertEqual(cpus, '0-13,28-41')

    def test_pci_to_numa_node(self):
        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(1, '0', ''))
        with self.assertRaises(ssh.SSHCommandError):
            self.cpuinfo.pci_to_numa_node(0)

        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(0, '0', ''))
        self.assertEqual(self.cpuinfo.pci_to_numa_node(0), 0)

    def test_pci_to_numa_node_negative(self):
        self.cpuinfo.connection.execute = mock.Mock(
            return_value=(0, '-1', ''))
        self.assertIsNone(self.cpuinfo.pci_to_numa_node(0))

    def test__format_ht_topo_cmd(self):
        cores = [0, 1, 2, 3, 4]
        cmd = self.cpuinfo._format_ht_topo_cmd(cores)
        expected = (
            'for i in 0 1 2 3 4; do '
            'echo "$i: $(cat /sys/devices/system/cpu/cpu$i/topology/thread_siblings_list)"; '
            'done'
        )
        self.assertEqual(cmd, expected)

    def test_ht_topo(self):
        cores = [0, 1, 2, 3, 4]
        self.cpuinfo.connection.execute = mock.Mock(return_value=(0, '', ''))
        self.cpuinfo._format_ht_topo_cmd = mock.Mock(return_value='cmd')
        self.cpuinfo.ht_topo(cores)

        self.cpuinfo.connection.execute = mock.Mock(return_value=(1, '', ''))
        self.cpuinfo._format_ht_topo_cmd = mock.Mock(return_value='cmd')
        with self.assertRaises(ssh.SSHCommandError):
            self.cpuinfo.ht_topo(cores)


class TestCpuModel(unittest.TestCase):
    def setUp(self):
        connection = mock.Mock()
        cpuinfo = CpuInfo(connection)
        self.cpu_model = CpuModel(cpuinfo)
        self.cpu_model.exclude_ht_cores = False

    def test_cpu_cores_pool(self):
        self.cpu_model.cpu_cores_pool = '1'
        self.assertEqual(str(self.cpu_model.cpu_cores_pool), '1')

    def test_allocate(self):
        cpus = self.cpu_model.allocate(None)
        self.assertEqual(cpus, None)

        cpus = self.cpu_model.allocate(0)
        self.assertEqual(cpus, CpuList([]))

        self.cpu_model.cpu_cores_pool = '1-10'
        cpus = self.cpu_model.allocate(2)
        self.assertEqual(cpus.mask, CpuList('1,2').mask)
        cpus = self.cpu_model.allocate(3)
        self.assertEqual(cpus.mask, CpuList('3,4,5').mask)
        self.assertEqual(str(self.cpu_model.cpu_cores_pool), '6-10')

        with self.assertRaises(CpuModelNotInPoolException):
            self.cpu_model.allocate(CpuList('10-20'))

        with self.assertRaises(CpuModelWrongArgument):
            self.cpu_model.allocate(1.1)


    def test_deallocate(self):
        self.cpu_model.cpu_cores_pool = '1-10'
        cpus_to_remove = self.cpu_model.allocate(2)
        self.cpu_model.allocate(3)
        self.cpu_model.deallocate(cpus_to_remove)
        self.assertEqual(str(self.cpu_model.cpu_cores_pool), '1,2,6-10')

    def test__remove_ht_cores(self):
        self.cpu_model.exclude_ht_cores = True
        self.cpu_model.cpuinfo.ht_topo = mock.Mock(return_value=EXAMPLE_HT_TOPO)
        self.cpu_model.cpu_cores_pool = CpuList([0, 1, 2, 3, 4, 5])
        expected = CpuList([0, 1, 2, 3])
        self.assertEqual(self.cpu_model.cpu_cores_pool, expected)
