# Copyright (c) 2015 Intel Research and Development Ireland Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Experimental Framework
"""

from __future__ import absolute_import
from distutils.core import setup


setup(name='apexlake',
      version='1.0',
      description='Framework to automatically run experiments/benchmarks '
                  'with VMs within OpenStack environments',
      author='Intel Research and Development Ireland Ltd',
      author_email='vincenzo.m.riccobene@intel.com',
      license='Apache 2.0',
      url='www.intel.com',
      packages=['experimental_framework',
                'experimental_framework.benchmarks',
                'experimental_framework.packet_generators',
                'experimental_framework.libraries',
                'experimental_framework.constants'],
      include_package_data=True,
      package_data={
          'experimental_framework': [
              'packet_generators/dpdk_pktgen/*.lua',
              'packet_generators/pcap_files/*.pcap',
              'packet_generators/pcap_files/*.sh',
              'libraries/packet_checker/*'
          ]
      },
      data_files=[
          ('/tmp/apexlake/', ['apexlake.conf']),
          ('/tmp/apexlake/heat_templates/',
           ['heat_templates/vTC.yaml']),
          ('/tmp/apexlake/heat_templates/',
           ['heat_templates/stress_workload.yaml']),
          ('/tmp/apexlake/heat_templates/',
           ['heat_templates/vTC_liberty.yaml']),
          ('/tmp/apexlake/heat_templates/',
           ['heat_templates/stress_workload_liberty.yaml'])
      ])
