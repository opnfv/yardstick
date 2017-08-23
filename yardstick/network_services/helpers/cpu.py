# Copyright (c) 2016-2017 Intel Corporation
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


import io


class CpuSysCores(object):

    def __init__(self, connection=""):
        self.core_map = {}
        self.connection = connection

    def _open_cpuinfo(self):
        cpuinfo = io.BytesIO()
        self.connection.get_file_obj("/proc/cpuinfo", cpuinfo)
        lines = cpuinfo.getvalue().decode('utf-8').splitlines()
        return lines

    def _get_core_details(self, lines):
        core_details = []
        core_lines = {}
        for line in lines:
            if line.strip():
                    name, value = line.split(":", 1)
                    core_lines[name.strip()] = value.strip()
            else:
                    core_details.append(core_lines)
                    core_lines = {}

        return core_details

    def get_core_socket(self):
        lines = self.connection.execute("lscpu")[1].split(u'\n')
        num_cores = self._get_core_details(lines)
        for num in num_cores:
            self.core_map["cores_per_socket"] = num["Core(s) per socket"]
            self.core_map["thread_per_core"] = num["Thread(s) per core"]

        lines = self._open_cpuinfo()
        core_details = self._get_core_details(lines)
        for core in core_details:
            for k, v in core.items():
                if k == "physical id":
                    if core["physical id"] not in self.core_map:
                        self.core_map[core['physical id']] = []
                    self.core_map[core['physical id']].append(
                        core["processor"])

        return self.core_map

    def validate_cpu_cfg(self, vnf_cfg=None):
        if vnf_cfg is None:
            vnf_cfg = {
                'lb_config': 'SW',
                'lb_count': 1,
                'worker_config': '1C/1T',
                'worker_threads': 1
            }
        if self.core_map["thread_per_core"] == 1 and \
                vnf_cfg["worker_config"] == "1C/2T":
            return -1

        if vnf_cfg['lb_config'] == 'SW':
            num_cpu = int(vnf_cfg["worker_threads"]) + 5
            if int(self.core_map["cores_per_socket"]) < num_cpu:
                return -1

        return 0
