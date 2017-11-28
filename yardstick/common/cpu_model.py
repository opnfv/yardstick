import StringIO
import copy
import re
import math
import io
from yardstick.ssh import SSHCommandError


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


class CpuList(set):
    def __init__(self, value=None):
        if isinstance(value, unicode):
            value = str(value)

        if isinstance(value, int):
            value = _mask_to_set(value)
        elif isinstance(value, str):
            converted = _string_to_set(value)
            if converted is None:
                converted = _mask_to_set(value)
            if converted is None:
                converted = _mask_to_set(value)
            if converted is None:
                raise TypeError("{} cannot be converted to a CPU list")
            value = converted
        if value is None:
            super(CpuList, self).__init__()
        else:
            super(CpuList, self).__init__(value)

    @property
    def mask(self):
        return _set_to_mask(self)

    def __str__(self):
        tmp_lst = sorted(self)
        out = StringIO.StringIO()
        hyphen = False
        seq_len = 0
        for i, e in enumerate(tmp_lst):
            if i == 0:
                out.write(str(e))
                continue
            if tmp_lst[i - 1] + 1 == e:
                hyphen = True
                seq_len += 1
                continue
            elif hyphen:
                hyphen = False
                if seq_len == 1:
                    out.write(',')
                else:
                    out.write('-')
                out.write(str(tmp_lst[i - 1]))
            out.write(',')
            out.write(str(e))
        else:
            if hyphen:
                out.write('-')
                out.write(str(e))
        return out.getvalue()


def _try_or_none(func):
    def f(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError):
            return None
    return f


@_try_or_none
def _set_to_mask(l):
    return sum(2 ** i for i in l)


@_try_or_none
def _mask_to_set(mask):
    # TODO is there a more effective implementation
    if isinstance(mask, str):
        try:
            mask = int(mask, 2)
        except ValueError:
            mask = int(mask, 16)
    cpus = set()
    i = 1
    while i <= mask:
        if i & mask:
            cpus.add(int(math.log(i, 2)))
        i <<= 1
    return cpus


class CpuInfoDict(object):
    def parse(self, input):
        self.cpu_list = []
        processor = {}
        for a_row in input.splitlines():
            if not a_row:
                self.cpu_list.append(copy.deepcopy(processor))
                processor = {}
                continue
            key, value = a_row.split(':')
            processor.update({key.strip(): value.strip()})

    def __init__(self, source):
        self.parse(source)


def expand(x):
    """accepts an integer or a range e.g. 3-5.
    Either returns that integer or a list of values in the given range including the boundaries
    """
    try:
        low, high = x.split('-')
        return range(int(low), int(high) + 1)
    except ValueError:
        return [int(x)]


@_try_or_none
def _string_to_set(s):
    o = []
    for i in s.split(','):
        o.extend(expand(i))
    return o


class CpuInfo(object):
    ISOLCPUS_RE = re.compile(r'^.* isolcpus=([^ ]+).*$')

    def __init__(self, connection):
        self.connection = connection
        self._cpuinfo = None
        self._lscpu = None
        self._isolcpus = None
        self._numa_cpus = {}
        self._pci_to_numa_node = {}

    @property
    def cpuinfo(self):
        if self._cpuinfo is not None:
            return self._cpuinfo
        cpuinfo = io.BytesIO()
        self.connection.get_file_obj("/proc/cpuinfo", cpuinfo)
        self._cpuinfo = CpuInfoDict(cpuinfo.getvalue().decode('utf-8'))
        return self._cpuinfo

    @property
    def lscpu(self):
        if self._lscpu is not None:
            return self._lscpu
        rv = self.connection.execute("lscpu")
        if rv[0] != 0:
            raise SSHCommandError('Cannot get lscpu info', rv)
        self._lscpu = {}
        for a_line in rv[1].splitlines():
            if not a_line:
                continue
            key, value = a_line.split(':')
            self._lscpu[key.strip()] = value.strip()
        return self._lscpu

    @property
    def isolcpus(self):
        if self._isolcpus is not None:
            return self._isolcpus
        rv = self.connection.execute('cat /proc/cmdline')
        if rv[0] != 0:
            raise SSHCommandError('Failed to read kernel command line', rv)
        cmdline = rv[1]
        m = re.match(self.ISOLCPUS_RE, cmdline)
        try:
            self._isolcpus = m.group(1)
        except AttributeError:
            self._isolcpus = None
        return self._isolcpus

    def _get_numa_node_for_pci(self, pci):
        # this will be handled by the dpdkbindhelper once it gets merged
        rv = self.connection.execute(
            'cat $(find /sys/devices/ -type d -name {})/numa_node'.format(pci))
        if rv[0] != 0:
            raise SSHCommandError('Failed to detect numa node for pci device', rv)
        numa_node = rv[1]
        if numa_node < 0:
            return None
        return numa_node

    def get_cpus_for_numa_node(self, numa_node):
        return self.lscpu['NUMA node{} CPU(s)'.format(numa_node)]

    def numa_node_to_cpus(self, numa_node):
        if self._numa_cpus.get(numa_node) is None:
            self._numa_cpus[numa_node] = self.get_cpus_for_numa_node(numa_node)
        return self._numa_cpus[numa_node]

    def pci_to_numa_node(self, pci):
        if self._pci_to_numa_node.get(pci) is None:
            self._pci_to_numa_node[pci] = int(self._get_numa_node_for_pci(pci))
        return self._pci_to_numa_node[pci]

    def _format_ht_topo_cmd(self, cores):
        return ('for i in {}; do '
                'echo "$i: $(cat /sys/devices/system/cpu/cpu$i/topology/thread_siblings_list)"; '
                'done'
                ).format(' '.join(str(core) for core in cores))

    def ht_topo(self, cores):
        cmd = self._format_ht_topo_cmd(cores)
        rv = self.connection.execute(cmd)
        if rv[0] > 0:
            raise SSHCommandError("Error finding hyperthreaded cores.", rv)
        return rv[1]


class CpuModel(object):
    def __init__(self, cpuinfo):
        self.cpuinfo = cpuinfo
        self.exclude_ht_cores = True
        self._cpu_core_pool = None

    @property
    def cpu_core_pool(self):
        return self._cpu_core_pool

    def _remove_ht_cores(self):
        cores = self._cpu_core_pool

        for line in self.cpuinfo.ht_topo(cores).splitlines():
            core, siblings = line.split(':')
            core = int(core)
            if core not in cores:
                continue
            siblings = [int(s) for s in siblings.split(',')]
            for sibling_core in siblings:
                if sibling_core == core:
                    continue
                if sibling_core in cores:
                    cores.remove(sibling_core)

    @cpu_core_pool.setter
    def cpu_core_pool(self, value):
        self._cpu_core_pool = CpuList(value)
        if self.exclude_ht_cores:
            self._remove_ht_cores()

    def allocate(self, cpus):
        print 'allocating {}'.format(cpus)
        if isinstance(cpus, int):
            number = cpus
        elif isinstance(cpus, CpuList):
            if cpus.issubset(self._cpu_core_pool):
                self._cpu_core_pool = self._cpu_core_pool.difference(cpus)
                return cpus
            raise Exception('Requested CPU is not in the pool')
        allocated = CpuList()
        for _ in range(number):
            allocated.add(self._cpu_core_pool.pop())
        return allocated

    def deallocate(self, cpu_set):
        """
        can throw ValueError exception in case there is not such mask
        """
        self._cpu_core_pool.update(cpu_set)

    @property
    def used_cpus(self):
        used_mask = 0
        for a_mask in self._masks:
            used_mask = used_mask | a_mask
        self._used_mask = used_mask
        return CpuList(used_mask)
