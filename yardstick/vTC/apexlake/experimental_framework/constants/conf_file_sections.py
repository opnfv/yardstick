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


# ------------------------------------------------------
# Configuration File Sections
# ------------------------------------------------------
CFS_PKTGEN = 'PacketGen'
CFS_GENERAL = 'General'
CFS_OPENSTACK = 'OpenStack'
CFS_EXPERIMENT_VNF = 'Experiment-VNF'
CFS_EXPERIMENT_GENERIC = 'Experiment-generic'
CFS_TESTCASE_PARAMETERS = 'Testcase-parameters'
CFS_DEPLOYMENT_PARAMETERS = 'Deployment-parameters'
CFS_INFLUXDB = 'InfluxDB'


def get_sections():
    return [
        CFS_PKTGEN,
        CFS_GENERAL,
        CFS_OPENSTACK,
        CFS_EXPERIMENT_VNF,
        # CFS_EXPERIMENT_GENERIC,
        CFS_TESTCASE_PARAMETERS,
        CFS_DEPLOYMENT_PARAMETERS,
        CFS_INFLUXDB
        # Add here eventually new sections in configuration file ...
    ]


def get_sections_api():
    return [
        CFS_PKTGEN,
        CFS_GENERAL,
        CFS_INFLUXDB
        # Add here eventually new sections in configuration file ...
    ]

# ------------------------------------------------------
# General section parameters
# ------------------------------------------------------
CFSG_ITERATIONS = 'iterations'
CFSG_TEMPLATE_DIR = 'template_dir'
CFSG_TEMPLATE_NAME = 'template_base_name'
CFSG_RESULT_DIRECTORY = 'results_directory'
CFSG_BENCHMARKS = 'benchmarks'
CFSG_DEBUG = 'debug'


# ------------------------------------------------------
# InfluxDB
# ------------------------------------------------------
CFSI_IDB_IP = 'influxdb_ip_address'
CFSI_IDB_PORT = 'influxdb_port'
CFSI_IDB_DB_NAME = 'influxdb_db_name'


# ------------------------------------------------------
# Packet generator section parameters
# ------------------------------------------------------
CFSP_PACKET_GENERATOR = 'packet_generator'
CFSP_DPDK_PKTGEN_DIRECTORY = 'pktgen_directory'
CFSP_DPDK_DPDK_DIRECTORY = 'dpdk_directory'
CFSP_DPDK_PROGRAM_NAME = 'program_name'
CFSP_DPDK_COREMASK = 'coremask'
CFSP_DPDK_MEMORY_CHANNEL = 'memory_channels'
CFSP_DPDK_BUS_SLOT_NIC_1 = 'bus_slot_nic_1'
CFSP_DPDK_BUS_SLOT_NIC_2 = 'bus_slot_nic_2'
CFSP_DPDK_NAME_IF_1 = 'name_if_1'
CFSP_DPDK_NAME_IF_2 = 'name_if_2'


# ------------------------------------------------------
# Supported Packet generators
# ------------------------------------------------------
CFSP_PG_NONE = 'none'
CFSP_PG_DPDK = 'dpdk_pktgen'


# ------------------------------------------------------
# OpenStack section variables
# ------------------------------------------------------
CFSO_IP_CONTROLLER = 'ip_controller'
CFSO_HEAT_URL = 'heat_url'
CFSO_USER = 'user'
CFSO_PASSWORD = 'password'
CFSO_AUTH_URI = 'auth_uri'
CFSO_PROJECT = 'project'
