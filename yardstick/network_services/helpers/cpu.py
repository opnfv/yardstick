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

# Number of threads per core.
NR_OF_THREADS = 2


class CpuSysCores(object):

    def __init__(self, connection=""):
        self.core_map = {}
        self.cpuinfo = {}
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
            for k, _ in core.items():
                if k == "physical id":
                    if core["physical id"] not in self.core_map:
                        self.core_map[core['physical id']] = []
                    self.core_map[core['physical id']].append(
                        core["processor"])

        return self.core_map

    def get_cpu_layout(self):
        _, stdout, _ = self.connection.execute("lscpu -p")
        self.cpuinfo = {}
        self.cpuinfo['cpuinfo'] = list()
        for line in stdout.split("\n"):
            if line and line[0] != "#":
                self.cpuinfo['cpuinfo'].append(
                    [CpuSysCores._str2int(x) for x in
                     line.split(",")])
        return self.cpuinfo

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

    def is_smt_enabled(self):
        return CpuSysCores.smt_enabled(self.cpuinfo)

    def cpu_list_per_node(self, cpu_node, smt_used=False):
        cpu_node = int(cpu_node)
        cpu_info = self.cpuinfo.get("cpuinfo")
        if cpu_info is None:
            raise RuntimeError("Node cpuinfo not available.")

        smt_enabled = self.is_smt_enabled()
        if not smt_enabled and smt_used:
            raise RuntimeError("SMT is not enabled.")

        cpu_list = []
        for cpu in cpu_info:
            if cpu[3] == cpu_node:
                cpu_list.append(cpu[0])

        if not smt_enabled or smt_enabled and smt_used:
            pass

        if smt_enabled and not smt_used:
            cpu_list_len = len(cpu_list)
            cpu_list = cpu_list[:int(cpu_list_len / NR_OF_THREADS)]

        return cpu_list

    def cpu_slice_of_list_per_node(self, cpu_node, skip_cnt=0, cpu_cnt=0,
                                   smt_used=False):
        cpu_list = self.cpu_list_per_node(cpu_node, smt_used)

        cpu_list_len = len(cpu_list)
        if cpu_cnt + skip_cnt > cpu_list_len:
            raise RuntimeError("cpu_cnt + skip_cnt > length(cpu list).")

        if cpu_cnt == 0:
            cpu_cnt = cpu_list_len - skip_cnt

        if smt_used:
            cpu_list_0 = cpu_list[:int(cpu_list_len / NR_OF_THREADS)]
            cpu_list_1 = cpu_list[int(cpu_list_len / NR_OF_THREADS):]
            cpu_list = [cpu for cpu in cpu_list_0[skip_cnt:skip_cnt + cpu_cnt]]
            cpu_list_ex = [cpu for cpu in
                           cpu_list_1[skip_cnt:skip_cnt + cpu_cnt]]
            cpu_list.extend(cpu_list_ex)
        else:
            cpu_list = [cpu for cpu in cpu_list[skip_cnt:skip_cnt + cpu_cnt]]

        return cpu_list

    def cpu_list_per_node_str(self, cpu_node, skip_cnt=0, cpu_cnt=0, sep=",",
                              smt_used=False):
        cpu_list = self.cpu_slice_of_list_per_node(cpu_node,
                                                   skip_cnt=skip_cnt,
                                                   cpu_cnt=cpu_cnt,
                                                   smt_used=smt_used)
        return sep.join(str(cpu) for cpu in cpu_list)

    @staticmethod
    def _str2int(string):
        try:
            return int(string)
        except ValueError:
            return 0

    @staticmethod
    def smt_enabled(cpuinfo):
        cpu_info = cpuinfo.get("cpuinfo")
        if cpu_info is None:
            raise RuntimeError("Node cpuinfo not available.")
        cpu_mems = [item[-4:] for item in cpu_info]
        cpu_mems_len = int(len(cpu_mems) / NR_OF_THREADS)
        count = 0
        for cpu_mem in cpu_mems[:cpu_mems_len]:
            if cpu_mem in cpu_mems[cpu_mems_len:]:
                count += 1
        return count == cpu_mems_len
