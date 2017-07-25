"""
vsperf2dashboard
"""
# Copyright 2015-2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import csv
import logging
import requests

def results2opnfv_dashboard(results_path, int_data):
    """
    the method open the csv file with results and calls json encoder
    """
    testcases = os.listdir(results_path)
    for test in testcases:
        if not ".csv" in test:
            continue
        resfile = results_path + '/' + test
        with open(resfile, 'r') as in_file:
            reader = csv.DictReader(in_file)
            _push_results(reader, int_data)

def _push_results(reader, int_data):
    """
    the method encodes results and sends them into opnfv dashboard
    """
    db_url = int_data['db_url']
    url = db_url + "/results"
    casename = ""
    version_ovs = ""
    version_dpdk = ""
    version = ""
    allowed_pkt = ["64", "128", "512", "1024", "1518"]
    details = {"64": '', "128": '', "512": '', "1024": '', "1518": ''}

    for row_reader in reader:
        if allowed_pkt.count(row_reader['packet_size']) == 0:
            logging.error("The framesize is not supported in opnfv dashboard")
            continue

        casename = _generate_test_name(row_reader['id'], int_data)
        if "back2back" in row_reader['id']:
            details[row_reader['packet_size']] = row_reader['b2b_frames']
        else:
            details[row_reader['packet_size']] = row_reader['throughput_rx_fps']

    # Create version field
    with open(int_data['pkg_list'], 'r') as pkg_file:
        for line in pkg_file:
            if "OVS_TAG" in line:
                version_ovs = line.replace(' ', '')
                version_ovs = version_ovs.replace('OVS_TAG?=', '')
            if "DPDK_TAG" in line:
                if int_data['vanilla'] is False:
                    version_dpdk = line.replace(' ', '')
                    version_dpdk = version_dpdk.replace('DPDK_TAG?=', '')
                else:
                    version_dpdk = "not used"
    version = "OVS " + version_ovs.replace('\n', '') + " DPDK " + version_dpdk.replace('\n', '')

    # Build body
    body = {"project_name": "vsperf",
            "case_name": casename,
            "pod_name": int_data['pod'],
            "installer": int_data['installer'],
            "version": version,
            "details": details}

    my_data = requests.post(url, json=body)
    logging.info("Results for %s sent to opnfv, http response: %s", casename, my_data)
    logging.debug("opnfv url: %s", db_url)
    logging.debug("the body sent to opnfv")
    logging.debug(body)

def _generate_test_name(testcase, int_data):
    """
    the method generates testcase name for releng
    """
    vanilla = int_data['vanilla']
    res_name = ""

    names = {'phy2phy_tput': ["tput_ovsdpdk", "tput_ovs"],
             'back2back': ["b2b_ovsdpdk", "b2b_ovs"],
             'phy2phy_tput_mod_vlan': ["tput_mod_vlan_ovsdpdk", "tput_mod_vlan_ovs"],
             'phy2phy_cont': ["cont_ovsdpdk", "cont_ovs"],
             'pvp_cont': ["pvp_cont_ovsdpdkuser", "pvp_cont_ovsvirtio"],
             'pvvp_cont': ["pvvp_cont_ovsdpdkuser", "pvvp_cont_ovsvirtio"],
             'phy2phy_scalability': ["scalability_ovsdpdk", "scalability_ovs"],
             'pvp_tput': ["pvp_tput_ovsdpdkuser", "pvp_tput_ovsvirtio"],
             'pvp_back2back': ["pvp_b2b_ovsdpdkuser", "pvp_b2b_ovsvirtio"],
             'pvvp_tput': ["pvvp_tput_ovsdpdkuser", "pvvp_tput_ovsvirtio"],
             'pvvp_back2back': ["pvvp_b2b_ovsdpdkuser", "pvvp_b2b_ovsvirtio"],
             'phy2phy_cpu_load': ["cpu_load_ovsdpdk", "cpu_load_ovs"],
             'phy2phy_mem_load': ["mem_load_ovsdpdk", "mem_load_ovs"]}

    for name, name_list in names.items():
        if name != testcase:
            continue
        if vanilla is True:
            res_name = name_list[1]
        else:
            res_name = name_list[0]
        break

    return res_name
