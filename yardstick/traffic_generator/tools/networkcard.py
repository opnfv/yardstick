# Copyright 2016-2017 Intel Corporation.
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

"""Tools for network card manipulation
"""

import os
import subprocess
import logging
import glob
from yardstick.traffic_generator.conf import settings

_LOGGER = logging.getLogger('tools.networkcard')

_PCI_DIR = '/sys/bus/pci/devices/{}/'
_SRIOV_NUMVFS = os.path.join(_PCI_DIR, 'sriov_numvfs')
_SRIOV_TOTALVFS = os.path.join(_PCI_DIR, 'sriov_totalvfs')
_SRIOV_VF_PREFIX = 'virtfn'
_SRIOV_PF = 'physfn'
_PCI_NET = 'net'
_PCI_DRIVER = 'driver'


def check_pci(pci_handle):
    """ Checks if given extended PCI handle has correct length and fixes
        it if possible.

    :param pci_handle: PCI slot identifier. It can contain vsperf specific
        suffix after '|' with VF indication. e.g. '0000:05:00.0|vf1'

    :returns: PCI handle
    """
    pci = pci_handle.split('|')
    pci_len = len(pci[0])
    if pci_len == 12:
        return pci_handle
    elif pci_len == 7:
        pci[0] = '0000:' + pci[0][-7:]
        _LOGGER.debug('Adding domain part to PCI slot %s', pci[0])
        return '|'.join(pci)
    elif pci_len > 12:
        pci[0] = pci[0][-12:]
        _LOGGER.warning('PCI slot is too long, it will be shortened to %s', pci[0])
        return '|'.join(pci)
    else:
        # pci_handle has a strange length, but let us try to use it
        _LOGGER.error('Unknown format of PCI slot %s', pci_handle)
        return pci_handle

def is_sriov_supported(pci_handle):
    """ Checks if sriov is supported by given NIC

    :param pci_handle: PCI slot identifier with domain part.

    :returns: True on success, False otherwise
    """
    return os.path.isfile(_SRIOV_TOTALVFS.format(pci_handle))

def is_sriov_nic(pci_handle):
    """ Checks if given extended PCI ID refers to the VF

    :param pci_handle: PCI slot identifier with domain part. It can contain
        vsperf specific suffix after '|' with VF indication.
        e.g. '0000:05:00.0|vf1'

    :returns: True on success, False otherwise
    """
    for item in pci_handle.split('|'):
        if item.lower().startswith('vf'):
            return True
    return False

def set_sriov_numvfs(pci_handle, numvfs):
    """ Checks if sriov is supported and configures given number of VFs

    :param pci_handle: PCI slot identifier with domain part.
    :param numvfs: Number of VFs to be configured at given NIC.

    :returns: True on success, False otherwise
    """
    if not is_sriov_supported(pci_handle):
        return False

    if get_sriov_numvfs(pci_handle) == numvfs:
        return True

    if numvfs and get_sriov_numvfs(pci_handle) != 0:
        if not set_sriov_numvfs(pci_handle, 0):
            return False

    try:
        subprocess.call('sudo bash -c "echo {} > {}"'.format(numvfs, _SRIOV_NUMVFS.format(pci_handle)), shell=True)
        return get_sriov_numvfs(pci_handle) == numvfs
    except OSError:
        _LOGGER.debug('Number of VFs cant be changed to %s for PF %s', numvfs, pci_handle)
        return False

def get_sriov_numvfs(pci_handle):
    """ Returns the number of configured VFs

    :param pci_handle: PCI slot identifier with domain part
    :returns: the number of configured VFs
    """
    if is_sriov_supported(pci_handle):
        with open(_SRIOV_NUMVFS.format(pci_handle), 'r') as numvfs:
            return int(numvfs.readline().rstrip('\n'))

    return None

def get_sriov_totalvfs(pci_handle):
    """ Checks if sriov is supported and returns max number of supported VFs

    :param pci_handle: PCI slot identifier with domain part
    :returns: the max number of supported VFs by given NIC
    """
    if is_sriov_supported(pci_handle):
        with open(_SRIOV_TOTALVFS.format(pci_handle), 'r') as total:
            return int(total.readline().rstrip('\n'))

    return None

def get_sriov_vfs_list(pf_pci_handle):
    """ Returns list of PCI handles of VFs configured at given NIC/PF

    :param pf_pci_handle: PCI slot identifier of PF with domain part.
    :returns: list
    """
    vfs = []
    if is_sriov_supported(pf_pci_handle):
        for vf_name in glob.glob(os.path.join(_PCI_DIR, _SRIOV_VF_PREFIX + '*').format(pf_pci_handle)):
            vfs.append(os.path.basename(os.path.realpath(vf_name)))

    return vfs

def get_sriov_pf(vf_pci_handle):
    """ Get PCI handle of PF which belongs to given VF

    :param vf_pci_handle: PCI slot identifier of VF with domain part.
    :returns: PCI handle of parent PF
    """
    pf_path = os.path.join(_PCI_DIR, _SRIOV_PF).format(vf_pci_handle)
    if os.path.isdir(pf_path):
        return os.path.basename(os.path.realpath(pf_path))

    return None

def get_driver(pci_handle):
    """ Returns name of kernel driver assigned to given NIC

    :param pci_handle: PCI slot identifier with domain part.
    :returns: string with assigned kernel driver, None otherwise
    """
    driver_path = os.path.join(_PCI_DIR, _PCI_DRIVER).format(pci_handle)
    if os.path.isdir(driver_path):
        return os.path.basename(os.path.realpath(driver_path))

    return None

def get_device_name(pci_handle):
    """ Returns name of network card device name

    :param pci_handle: PCI slot identifier with domain part.
    :returns: string with assigned NIC device name, None otherwise
    """
    net_path = os.path.join(_PCI_DIR, _PCI_NET).format(pci_handle)
    try:
        return os.listdir(net_path)[0]
    except FileNotFoundError:
        return None
    except IndexError:
        return None

    return None

def get_mac(pci_handle):
    """ Returns MAC address of given NIC

    :param pci_handle: PCI slot identifier with domain part.
    :returns: string with assigned MAC address, None otherwise
    """
    mac_path = glob.glob(os.path.join(_PCI_DIR, _PCI_NET, '*', 'address').format(pci_handle))
    # kernel driver is loaded and MAC can be read
    if len(mac_path) and os.path.isfile(mac_path[0]):
        with open(mac_path[0], 'r') as _file:
            return _file.readline().rstrip('\n')

    # MAC address is unknown, e.g. NIC is assigned to DPDK
    return None

def get_nic_info(full_pci_handle):
    """ Parse given pci handle with additional info and returns
        requested NIC info.

    :param full_pci_handle: A string with extended network card PCI ID.
        extended PCI ID syntax: PCI_ID[|vfx][|(mac|dev)]
        examples:
            0000:06:00.0            - returns the same value
            0000:06:00.0|vf0        - returns PCI ID of 1st virtual function of given NIC
            0000:06:00.0|mac        - returns MAC address of given NIC
            0000:06:00.0|vf0|mac    - returns MAC address of 1st virtual function of given NIC

    :returns: A string with requested NIC data or None if data cannot be read.
    """
    parsed_handle = full_pci_handle.split('|')
    if len(parsed_handle) not in (1, 2, 3):
        _LOGGER.error("Invalid PCI device name: '%s'", full_pci_handle)
        return None

    pci_handle = parsed_handle[0]

    for action in parsed_handle[1:]:
        # in case of SRIOV get PCI handle of given virtual function
        if action.lower().startswith('vf'):
            try:
                vf_num = int(action[2:])
                pci_handle = get_sriov_vfs_list(pci_handle)[vf_num]
            except ValueError:
                _LOGGER.error("Pci device '%s', does not have VF with index '%s'", pci_handle, action[2:])
                return None
            except IndexError:
                _LOGGER.error("Pci device '%s', does not have VF with index '%s'", pci_handle, vf_num)
                return None
            continue

        # return requested info for given PCI handle
        if action.lower() == 'mac':
            return get_mac(pci_handle)
        elif action.lower() == 'dev':
            return get_device_name(pci_handle)
        else:
            _LOGGER.error("Invalid item '%s' in PCI handle '%s'", action, full_pci_handle)
            return None

    return pci_handle

def reinit_vfs(pf_pci_handle):
    """ Reinitializates all VFs, which belong to given PF

    :param pf_pci_handle: PCI slot identifier of PF with domain part.
    """
    rte_pci_tool = settings.getValue('TOOLS')['bind-tool']

    for vf_nic in get_sriov_vfs_list(pf_pci_handle):
        nic_driver = get_driver(vf_nic)
        if nic_driver:
            try:
                subprocess.call(['sudo', rte_pci_tool, '--unbind', vf_nic],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.call(['sudo', rte_pci_tool, '--bind=' + nic_driver, vf_nic],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                _LOGGER.warning('Error during reinitialization of VF %s', vf_nic)
        else:
            _LOGGER.warning("Can't detect driver for VF %s", vf_nic)
