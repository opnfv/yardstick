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


from __future__ import absolute_import
from experimental_framework.constants import conf_file_sections as cfs

# ------------------------------------------------------
# Directories and file locations
# ------------------------------------------------------
EXPERIMENTAL_FRAMEWORK_DIR = 'experimental_framework/'
EXPERIMENT_TEMPLATE_NAME = 'experiment'
TEMPLATE_FILE_EXTENSION = '.yaml'
DPDK_PKTGEN_DIR = 'packet_generators/dpdk_pktgen/'
PCAP_DIR = 'packet_generators/pcap_files/'


def get_supported_packet_generators():
    return [
        cfs.CFSP_PG_NONE,
        cfs.CFSP_PG_DPDK
        # Add here any other supported packet generator
    ]
