##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Unittest for yardstick.common.utils

from __future__ import absolute_import

import ipaddress
import os
import unittest
from copy import deepcopy
from itertools import product, chain

import mock
from six.moves import configparser

import yardstick
from yardstick.common import utils
from yardstick.common import constants


class IterSubclassesTestCase(unittest.TestCase):
    # Disclaimer: this class is a modified copy from
    # rally/tests/unit/common/plugin/test_discover.py
    # Copyright 2015: Mirantis Inc.

    def test_itersubclasses(self):
        class A(object):
            pass

        class B(A):
            pass

        class C(A):
            pass

        class D(C):
            pass

        self.assertEqual([B, C, D], list(utils.itersubclasses(A)))


class ImportModulesFromPackageTestCase(unittest.TestCase):

    @mock.patch('yardstick.common.utils.os.walk')
    def test_import_modules_from_package_no_mod(self, mock_walk):
        yardstick_root = os.path.dirname(os.path.dirname(yardstick.__file__))
        mock_walk.return_value = ([
            (os.path.join(yardstick_root, 'foo'), ['bar'], ['__init__.py']),
            (os.path.join(yardstick_root, 'foo', 'bar'), [], ['baz.txt', 'qux.rst'])
        ])

        utils.import_modules_from_package('foo.bar')

    @mock.patch('yardstick.common.utils.os.walk')
    @mock.patch('yardstick.common.utils.importutils')
    def test_import_modules_from_package(self, mock_importutils, mock_walk):

        yardstick_root = os.path.dirname(os.path.dirname(yardstick.__file__))
        mock_walk.return_value = ([
            (os.path.join(yardstick_root, 'foo', os.pardir, 'bar'), [], ['baz.py'])
        ])

        utils.import_modules_from_package('foo.bar')
        mock_importutils.import_module.assert_called_with('bar.baz')


class GetParaFromYaml(unittest.TestCase):

    @mock.patch('yardstick.common.utils.os.environ.get')
    def test_get_param_para_not_found(self, get_env):
        file_path = 'config_sample.yaml'
        get_env.return_value = self._get_file_abspath(file_path)
        args = 'releng.file'
        default = 'hello'
        self.assertTrue(constants.get_param(args, default), default)

    @mock.patch('yardstick.common.utils.os.environ.get')
    def test_get_param_para_exists(self, get_env):
        file_path = 'config_sample.yaml'
        get_env.return_value = self._get_file_abspath(file_path)
        args = 'releng.dir'
        para = '/home/opnfv/repos/releng'
        self.assertEqual(para, constants.get_param(args))

    def _get_file_abspath(self, filename):
        curr_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(curr_path, filename)
        return file_path


class CommonUtilTestCase(unittest.TestCase):

    def setUp(self):
        self.data = {
            "benchmark": {
                "data": {
                    "mpstat": {
                        "cpu0": {
                            "%sys": "0.00",
                            "%idle": "99.00"
                        },
                        "loadavg": [
                            "1.09",
                            "0.29"
                        ]
                    },
                    "rtt": "1.03"
                }
            }
        }

    def test__dict_key_flatten(self):
        line = 'mpstat.loadavg1=0.29,rtt=1.03,mpstat.loadavg0=1.09,' \
               'mpstat.cpu0.%idle=99.00,mpstat.cpu0.%sys=0.00'
        # need to sort for assert to work
        line = ",".join(sorted(line.split(',')))
        flattened_data = utils.flatten_dict_key(
            self.data['benchmark']['data'])
        result = ",".join(
            ("=".join(item) for item in sorted(flattened_data.items())))
        self.assertEqual(result, line)


class TestMacAddressToHex(unittest.TestCase):

    def test_mac_address_to_hex_list(self):
        self.assertEqual(utils.mac_address_to_hex_list("ea:3e:e1:9a:99:e8"),
                         ['0xea', '0x3e', '0xe1', '0x9a', '0x99', '0xe8'])


class TranslateToStrTestCase(unittest.TestCase):

    def test_translate_to_str_unicode(self):
        input_str = u'hello'
        output_str = utils.translate_to_str(input_str)

        result = 'hello'
        self.assertEqual(result, output_str)

    def test_translate_to_str_dict_list_unicode(self):
        input_str = {
            u'hello': {u'hello': [u'world']}
        }
        output_str = utils.translate_to_str(input_str)

        result = {
            'hello': {'hello': ['world']}
        }
        self.assertEqual(result, output_str)

    def test_translate_to_str_non_string(self):
        input_value = object()
        result = utils.translate_to_str(input_value)
        self.assertIs(input_value, result)


class TestParseCpuInfo(unittest.TestCase):

    def test_single_socket_no_hyperthread(self):
        cpuinfo = """\
processor       : 2
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel Core Processor (Haswell, no TSX)
stepping        : 1
microcode       : 0x1
cpu MHz         : 2294.684
cache size      : 4096 KB
physical id     : 0
siblings        : 5
core id         : 2
cpu cores       : 5
apicid          : 2
initial apicid  : 2
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl eagerfpu pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt arat
bugs            :
bogomips        : 4589.36
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 3
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel Core Processor (Haswell, no TSX)
stepping        : 1
microcode       : 0x1
cpu MHz         : 2294.684
cache size      : 4096 KB
physical id     : 0
siblings        : 5
core id         : 3
cpu cores       : 5
apicid          : 3
initial apicid  : 3
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl eagerfpu pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt arat
bugs            :
bogomips        : 4589.36
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 4
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel Core Processor (Haswell, no TSX)
stepping        : 1
microcode       : 0x1
cpu MHz         : 2294.684
cache size      : 4096 KB
physical id     : 0
siblings        : 5
core id         : 4
cpu cores       : 5
apicid          : 4
initial apicid  : 4
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc rep_good nopl eagerfpu pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt arat
bugs            :
bogomips        : 4589.36
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

"""
        socket_map = utils.SocketTopology.parse_cpuinfo(cpuinfo)
        assert sorted(socket_map.keys()) == [0]
        assert sorted(socket_map[0].keys()) == [2, 3, 4]

    def test_single_socket_hyperthread(self):
        cpuinfo = """\
processor       : 5
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Xeon(R) CPU E3-1275 v3 @ 3.50GHz
stepping        : 3
microcode       : 0x1d
cpu MHz         : 3501.708
cache size      : 8192 KB
physical id     : 0
siblings        : 8
core id         : 1
cpu cores       : 4
apicid          : 3
initial apicid  : 3
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm epb tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts
bugs            :
bogomips        : 6987.36
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

processor       : 6
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Xeon(R) CPU E3-1275 v3 @ 3.50GHz
stepping        : 3
microcode       : 0x1d
cpu MHz         : 3531.829
cache size      : 8192 KB
physical id     : 0
siblings        : 8
core id         : 2
cpu cores       : 4
apicid          : 5
initial apicid  : 5
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm epb tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts
bugs            :
bogomips        : 6987.36
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

processor       : 7
vendor_id       : GenuineIntel
cpu family      : 6
model           : 60
model name      : Intel(R) Xeon(R) CPU E3-1275 v3 @ 3.50GHz
stepping        : 3
microcode       : 0x1d
cpu MHz         : 3500.213
cache size      : 8192 KB
physical id     : 0
siblings        : 8
core id         : 3
cpu cores       : 4
apicid          : 7
initial apicid  : 7
fpu             : yes
fpu_exception   : yes
cpuid level     : 13
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm epb tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid xsaveopt dtherm ida arat pln pts
bugs            :
bogomips        : 6987.24
clflush size    : 64
cache_alignment : 64
address sizes   : 39 bits physical, 48 bits virtual
power management:

"""
        socket_map = utils.SocketTopology.parse_cpuinfo(cpuinfo)
        assert sorted(socket_map.keys()) == [0]
        assert sorted(socket_map[0].keys()) == [1, 2, 3]
        assert sorted(socket_map[0][1]) == [5]
        assert sorted(socket_map[0][2]) == [6]
        assert sorted(socket_map[0][3]) == [7]

    def test_dual_socket_hyperthread(self):
        cpuinfo = """\
processor       : 1
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.976
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 1
cpu cores       : 22
apicid          : 2
initial apicid  : 2
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4401.07
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 2
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1226.892
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 2
cpu cores       : 22
apicid          : 4
initial apicid  : 4
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4400.84
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 43
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 28
cpu cores       : 22
apicid          : 120
initial apicid  : 120
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4411.31
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 44
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 0
cpu cores       : 22
apicid          : 1
initial apicid  : 1
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4410.61
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 85
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.573
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 26
cpu cores       : 22
apicid          : 117
initial apicid  : 117
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4409.07
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 86
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 27
cpu cores       : 22
apicid          : 119
initial apicid  : 119
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4406.62
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 87
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.708
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 28
cpu cores       : 22
apicid          : 121
initial apicid  : 121
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4413.48
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

"""
        socket_map = utils.SocketTopology.parse_cpuinfo(cpuinfo)
        assert sorted(socket_map.keys()) == [0, 1]
        assert sorted(socket_map[0].keys()) == [0, 1, 2]
        assert sorted(socket_map[1].keys()) == [26, 27, 28]
        assert sorted(socket_map[0][0]) == [44]
        assert sorted(socket_map[0][1]) == [1]
        assert sorted(socket_map[0][2]) == [2]
        assert sorted(socket_map[1][26]) == [85]
        assert sorted(socket_map[1][27]) == [86]
        assert sorted(socket_map[1][28]) == [43, 87]

    def test_dual_socket_no_hyperthread(self):
        cpuinfo = """\
processor       : 1
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.976
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 1
cpu cores       : 22
apicid          : 2
initial apicid  : 2
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4401.07
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 2
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1226.892
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 2
cpu cores       : 22
apicid          : 4
initial apicid  : 4
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4400.84
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 43
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 28
cpu cores       : 22
apicid          : 120
initial apicid  : 120
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4411.31
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 44
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 0
siblings        : 44
core id         : 0
cpu cores       : 22
apicid          : 1
initial apicid  : 1
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4410.61
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 85
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.573
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 26
cpu cores       : 22
apicid          : 117
initial apicid  : 117
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4409.07
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 86
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.305
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 27
cpu cores       : 22
apicid          : 119
initial apicid  : 119
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4406.62
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

processor       : 87
vendor_id       : GenuineIntel
cpu family      : 6
model           : 79
model name      : Intel(R) Xeon(R) CPU E5-2699 v4 @ 2.20GHz
stepping        : 1
microcode       : 0xb00001f
cpu MHz         : 1200.708
cache size      : 56320 KB
physical id     : 1
siblings        : 44
core id         : 28
cpu cores       : 22
apicid          : 121
initial apicid  : 121
fpu             : yes
fpu_exception   : yes
cpuid level     : 20
wp              : yes
flags           : fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb cat_l3 cdp_l3 intel_ppin intel_pt tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm cqm rdt_a rdseed adx smap xsaveopt cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts
bugs            :
bogomips        : 4413.48
clflush size    : 64
cache_alignment : 64
address sizes   : 46 bits physical, 48 bits virtual
power management:

"""
        socket_map = utils.SocketTopology.parse_cpuinfo(cpuinfo)
        processors = socket_map.processors()
        assert processors == [1, 2, 43, 44, 85, 86, 87]
        cores = socket_map.cores()
        assert cores == [0, 1, 2, 26, 27, 28]
        sockets = socket_map.sockets()
        assert sockets == [0, 1]


class ChangeObjToDictTestCase(unittest.TestCase):

    def test_change_obj_to_dict(self):
        class A(object):
            def __init__(self):
                self.name = 'yardstick'

        obj = A()
        obj_r = utils.change_obj_to_dict(obj)
        obj_s = {'name': 'yardstick'}
        self.assertEqual(obj_r, obj_s)


class SetDictValueTestCase(unittest.TestCase):

    def test_set_dict_value(self):
        input_dic = {
            'hello': 'world'
        }
        output_dic = utils.set_dict_value(input_dic, 'welcome.to', 'yardstick')
        self.assertEqual(output_dic.get('welcome', {}).get('to'), 'yardstick')


class RemoveFileTestCase(unittest.TestCase):

    def test_remove_file(self):
        try:
            utils.remove_file('notexistfile.txt')
        except Exception as e:
            self.assertTrue(isinstance(e, OSError))


class TestUtils(unittest.TestCase):

    @mock.patch('yardstick.common.utils.jsonify')
    def test_result_handler(self, mock_jsonify):
        mock_jsonify.return_value = 432

        self.assertEqual(utils.result_handler('x', 234), 432)
        mock_jsonify.assert_called_once_with({'status': 'x', 'result': 234})

    @mock.patch('random.randint')
    @mock.patch('socket.socket')
    def test_get_free_port(self, mock_socket, mock_randint):
        mock_randint.return_value = 7777
        s = mock_socket('x', 'y')
        s.connect_ex.side_effect = iter([0, 1])
        result = utils.get_free_port('10.20.30.40')
        self.assertEqual(result, 7777)
        self.assertEqual(s.connect_ex.call_count, 2)

    @mock.patch('subprocess.check_output')
    def test_execute_command(self, mock_check_output):
        expected = ['hello world', '1234']
        mock_check_output.return_value = os.linesep.join(expected)
        result = utils.execute_command('my_command arg1 arg2')
        self.assertEqual(result, expected)

    @mock.patch('subprocess.Popen')
    def test_source_env(self, mock_popen):
        base_env = deepcopy(os.environ)
        mock_process = mock_popen()
        output_list = [
            'garbage line before',
            'NEW_ENV_VALUE=234',
            'garbage line after',
        ]
        mock_process.communicate.return_value = os.linesep.join(output_list), '', 0
        expected = {'NEW_ENV_VALUE': '234'}
        result = utils.source_env('my_file')
        self.assertDictEqual(result, expected)
        os.environ.clear()
        os.environ.update(base_env)

    @mock.patch('yardstick.common.utils.configparser.ConfigParser')
    def test_parse_ini_file(self, mock_config_parser_type):
        defaults = {
            'default1': 'value1',
            'default2': 'value2',
        }
        s1 = {
            'key1': 'value11',
            'key2': 'value22',
        }
        s2 = {
            'key1': 'value123',
            'key2': 'value234',
        }

        mock_config_parser = mock_config_parser_type()
        mock_config_parser.read.return_value = True
        mock_config_parser.sections.return_value = ['s1', 's2']
        mock_config_parser.items.side_effect = iter([
            defaults.items(),
            s1.items(),
            s2.items(),
        ])

        expected = {
            'DEFAULT': defaults,
            's1': s1,
            's2': s2,
        }
        result = utils.parse_ini_file('my_path')
        self.assertDictEqual(result, expected)

    @mock.patch('yardstick.common.utils.configparser.ConfigParser')
    def test_parse_ini_file_missing_section_header(self, mock_config_parser_type):
        mock_config_parser = mock_config_parser_type()
        mock_config_parser.read.side_effect = \
            configparser.MissingSectionHeaderError(mock.Mock(), 321, mock.Mock())

        with self.assertRaises(configparser.MissingSectionHeaderError):
            utils.parse_ini_file('my_path')

    @mock.patch('yardstick.common.utils.configparser.ConfigParser')
    def test_parse_ini_file_no_file(self, mock_config_parser_type):
        mock_config_parser = mock_config_parser_type()
        mock_config_parser.read.return_value = False
        with self.assertRaises(RuntimeError):
            utils.parse_ini_file('my_path')

    @mock.patch('yardstick.common.utils.configparser.ConfigParser')
    def test_parse_ini_file_no_default_section_header(self, mock_config_parser_type):
        s1 = {
            'key1': 'value11',
            'key2': 'value22',
        }
        s2 = {
            'key1': 'value123',
            'key2': 'value234',
        }

        mock_config_parser = mock_config_parser_type()
        mock_config_parser.read.return_value = True
        mock_config_parser.sections.return_value = ['s1', 's2']
        mock_config_parser.items.side_effect = iter([
            configparser.NoSectionError(mock.Mock()),
            s1.items(),
            s2.items(),
        ])

        expected = {
            'DEFAULT': {},
            's1': s1,
            's2': s2,
        }
        result = utils.parse_ini_file('my_path')
        self.assertDictEqual(result, expected)

    def test_join_non_strings(self):
        self.assertEqual(utils.join_non_strings(':'), '')
        self.assertEqual(utils.join_non_strings(':', 'a'), 'a')
        self.assertEqual(utils.join_non_strings(':', 'a', 2, 'c'), 'a:2:c')
        self.assertEqual(utils.join_non_strings(':', ['a', 2, 'c']), 'a:2:c')
        self.assertEqual(utils.join_non_strings(':', 'abc'), 'abc')

    def test_validate_non_string_sequence(self):
        self.assertEqual(utils.validate_non_string_sequence([1, 2, 3]), [1, 2, 3])
        self.assertIsNone(utils.validate_non_string_sequence('123'))
        self.assertIsNone(utils.validate_non_string_sequence(1))

        self.assertEqual(utils.validate_non_string_sequence(1, 2), 2)
        self.assertEqual(utils.validate_non_string_sequence(1, default=2), 2)

        with self.assertRaises(RuntimeError):
            utils.validate_non_string_sequence(1, raise_exc=RuntimeError)

    def test_error_class(self):
        with self.assertRaises(RuntimeError):
            utils.ErrorClass()

        error_instance = utils.ErrorClass(test='')
        with self.assertRaises(AttributeError):
            error_instance.get_name()


class TestUtilsIpAddrMethods(unittest.TestCase):

    GOOD_IP_V4_ADDRESS_STR_LIST = [
        u'0.0.0.0',
        u'10.20.30.40',
        u'127.0.0.1',
        u'10.20.30.40',
        u'172.29.50.75',
        u'192.168.230.9',
        u'255.255.255.255',
    ]

    GOOD_IP_V4_MASK_STR_LIST = [
        u'/1',
        u'/8',
        u'/13',
        u'/19',
        u'/24',
        u'/32',
    ]

    GOOD_IP_V6_ADDRESS_STR_LIST = [
        u'::1',
        u'fe80::250:56ff:fe89:91ff',
        u'123:4567:89ab:cdef:123:4567:89ab:cdef',
    ]

    GOOD_IP_V6_MASK_STR_LIST = [
        u'/1',
        u'/16',
        u'/29',
        u'/64',
        u'/99',
        u'/128',
    ]

    INVALID_IP_ADDRESS_STR_LIST = [
        1,
        u'w.x.y.z',
        u'10.20.30.40/33',
        u'123:4567:89ab:cdef:123:4567:89ab:cdef/129',
    ]

    def test_safe_ip_address(self):
        addr_list = self.GOOD_IP_V4_ADDRESS_STR_LIST
        for addr in addr_list:
            # test with no mask
            expected = ipaddress.ip_address(addr)
            self.assertEqual(utils.safe_ip_address(addr), expected, addr)

    def test_safe_ip_address_v6_ip(self):
        addr_list = self.GOOD_IP_V6_ADDRESS_STR_LIST
        for addr in addr_list:
            # test with no mask
            expected = ipaddress.ip_address(addr)
            self.assertEqual(utils.safe_ip_address(addr), expected, addr)

    @mock.patch("yardstick.common.utils.logging")
    def test_safe_ip_address_negative(self, mock_logging):
        for value in self.INVALID_IP_ADDRESS_STR_LIST:
            self.assertIsNone(utils.safe_ip_address(value), value)

        addr_list = self.GOOD_IP_V4_ADDRESS_STR_LIST
        mask_list = self.GOOD_IP_V4_MASK_STR_LIST
        for addr_mask_pair in product(addr_list, mask_list):
            value = ''.join(addr_mask_pair)
            self.assertIsNone(utils.safe_ip_address(value), value)

        addr_list = self.GOOD_IP_V6_ADDRESS_STR_LIST
        mask_list = self.GOOD_IP_V6_MASK_STR_LIST
        for addr_mask_pair in product(addr_list, mask_list):
            value = ''.join(addr_mask_pair)
            self.assertIsNone(utils.safe_ip_address(value), value)

    def test_get_ip_version(self):
        addr_list = self.GOOD_IP_V4_ADDRESS_STR_LIST
        for addr in addr_list:
            # test with no mask
            self.assertEqual(utils.get_ip_version(addr), 4, addr)

    def test_get_ip_version_v6_ip(self):
        addr_list = self.GOOD_IP_V6_ADDRESS_STR_LIST
        for addr in addr_list:
            # test with no mask
            self.assertEqual(utils.get_ip_version(addr), 6, addr)

    @mock.patch("yardstick.common.utils.logging")
    def test_get_ip_version_negative(self, mock_logging):
        for value in self.INVALID_IP_ADDRESS_STR_LIST:
            self.assertIsNone(utils.get_ip_version(value), value)

        addr_list = self.GOOD_IP_V4_ADDRESS_STR_LIST
        mask_list = self.GOOD_IP_V4_MASK_STR_LIST
        for addr_mask_pair in product(addr_list, mask_list):
            value = ''.join(addr_mask_pair)
            self.assertIsNone(utils.get_ip_version(value), value)

        addr_list = self.GOOD_IP_V6_ADDRESS_STR_LIST
        mask_list = self.GOOD_IP_V6_MASK_STR_LIST
        for addr_mask_pair in product(addr_list, mask_list):
            value = ''.join(addr_mask_pair)
            self.assertIsNone(utils.get_ip_version(value), value)

    def test_ip_to_hex(self):
        self.assertEqual(utils.ip_to_hex('0.0.0.0'), '00000000')
        self.assertEqual(utils.ip_to_hex('10.20.30.40'), '0a141e28')
        self.assertEqual(utils.ip_to_hex('127.0.0.1'), '7f000001')
        self.assertEqual(utils.ip_to_hex('172.31.90.100'), 'ac1f5a64')
        self.assertEqual(utils.ip_to_hex('192.168.254.253'), 'c0a8fefd')
        self.assertEqual(utils.ip_to_hex('255.255.255.255'), 'ffffffff')

    def test_ip_to_hex_v6_ip(self):
        for value in self.GOOD_IP_V6_ADDRESS_STR_LIST:
            self.assertEqual(utils.ip_to_hex(value), value)

    @mock.patch("yardstick.common.utils.logging")
    def test_ip_to_hex_negative(self, mock_logging):
        addr_list = self.GOOD_IP_V4_ADDRESS_STR_LIST
        mask_list = self.GOOD_IP_V4_MASK_STR_LIST
        value_iter = (''.join(pair) for pair in product(addr_list, mask_list))
        for value in chain(value_iter, self.INVALID_IP_ADDRESS_STR_LIST):
            self.assertEqual(utils.ip_to_hex(value), value)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
