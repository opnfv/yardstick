##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import tempfile
import logging
import collections

from oslo_serialization import jsonutils

from yardstick.service import Service
from yardstick.common.exceptions import MissingPodInfoError
from yardstick.common.exceptions import UnsupportedPodFormatError
from yardstick.common.ansible_common import AnsibleCommon

LOG = logging.getLogger(__name__)


class Environment(Service):
    def __init__(self, pod=None):
        super(Environment, self).__init__()
        # pod can be a dict or a json format string
        self.pod = pod

    def get_sut_info(self):
        temdir = tempfile.mkdtemp(prefix='sut')

        nodes = self._load_pod_info()
        ansible = AnsibleCommon(nodes=nodes)
        ansible.gen_inventory_ini_dict()
        sut_info = ansible.get_sut_info(temdir)

        return self._format_sut_info(sut_info)

    def _load_pod_info(self):
        if self.pod is None:
            raise MissingPodInfoError

        if isinstance(self.pod, collections.Mapping):
            try:
                return self.pod['nodes']
            except KeyError:
                raise UnsupportedPodFormatError

        try:
            return jsonutils.loads(self.pod)['nodes']
        except (ValueError, KeyError):
            raise UnsupportedPodFormatError

    def _format_sut_info(self, sut_info):
        return {k: self._format_node_info(v) for k, v in sut_info.items()}

    def _format_node_info(self, node_info):
        info = []
        facts = node_info.get('ansible_facts', {})

        info.append(['hostname', facts.get('ansible_hostname')])

        info.append(['product_name', facts.get('ansible_product_name')])
        info.append(['product_version', facts.get('ansible_product_version')])

        processors = facts.get('ansible_processor', [])
        try:
            processor_type = '{} {}'.format(processors[0], processors[1])
        except IndexError:
            LOG.exception('No Processor in SUT data')
            processor_type = None

        info.append(['processor_type', processor_type])
        info.append(['architecture', facts.get('ansible_architecture')])
        info.append(['processor_cores', facts.get('ansible_processor_cores')])
        info.append(['processor_vcpus', facts.get('ansible_processor_vcpus')])

        memory = facts.get('ansible_memtotal_mb')
        memory = round(memory * 1.0 / 1024, 2) if memory else None
        info.append(['memory', '{} GB'.format(memory)])

        devices = facts.get('ansible_devices', {})
        info.extend([self._get_device_info(k, v) for k, v in devices.items()])

        lsb_description = facts.get('ansible_lsb', {}).get('description')
        info.append(['OS', lsb_description])

        interfaces = facts.get('ansible_interfaces')
        info.append(['interfaces', interfaces])
        if isinstance(interfaces, collections.Sequence):
            info.extend([self._get_interface_info(facts, i) for i in interfaces])
        info = [i for i in info if i]

        return info

    def _get_interface_info(self, facts, name):
        mac = facts.get('ansible_{}'.format(name), {}).get('macaddress')
        return [name, mac] if mac else []

    def _get_device_info(self, name, info):
        return ['disk_{}'.format(name), info.get('size')]
