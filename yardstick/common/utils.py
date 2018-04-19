# Copyright 2013: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
from contextlib import closing
import datetime
import errno
import importlib
import ipaddress
import logging
import os
import random
import re
import signal
import socket
import subprocess
import sys
import time

import six
from flask import jsonify
from six.moves import configparser
from oslo_serialization import jsonutils
from oslo_utils import encodeutils

import yardstick
from yardstick.common import exceptions


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Decorator for cli-args
def cliargs(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def itersubclasses(cls, _seen=None):
    """Generator over all subclasses of a given class in depth first order."""

    if not isinstance(cls, type):
        raise TypeError("itersubclasses must be called with "
                        "new-style classes, not %.100r" % cls)
    _seen = _seen or set()
    try:
        subs = cls.__subclasses__()
    except TypeError:   # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub


def import_modules_from_package(package, raise_exception=False):
    """Import modules given a package name

    :param: package - Full package name. For example: rally.deploy.engines
    """
    yardstick_root = os.path.dirname(os.path.dirname(yardstick.__file__))
    path = os.path.join(yardstick_root, *package.split('.'))
    for root, _, files in os.walk(path):
        matches = (filename for filename in files if filename.endswith('.py')
                   and not filename.startswith('__'))
        new_package = os.path.relpath(root, yardstick_root).replace(os.sep,
                                                                    '.')
        module_names = set(
            '{}.{}'.format(new_package, filename.rsplit('.py', 1)[0])
            for filename in matches)
        # Find modules which haven't already been imported
        missing_modules = module_names.difference(sys.modules)
        logger.debug('Importing modules: %s', missing_modules)
        for module_name in missing_modules:
            try:
                importlib.import_module(module_name)
            except (ImportError, SyntaxError) as exc:
                if raise_exception:
                    raise exc
                logger.exception('Unable to import module %s', module_name)


NON_NONE_DEFAULT = object()


def get_key_with_default(data, key, default=NON_NONE_DEFAULT):
    value = data.get(key, default)
    if value is NON_NONE_DEFAULT:
        raise KeyError(key)
    return value


def make_dict_from_map(data, key_map):
    return {dest_key: get_key_with_default(data, src_key, default)
            for dest_key, (src_key, default) in key_map.items()}


def makedirs(d):
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def remove_file(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def execute_command(cmd, **kwargs):
    exec_msg = "Executing command: '%s'" % cmd
    logger.debug(exec_msg)

    output = subprocess.check_output(cmd.split(), **kwargs)
    return encodeutils.safe_decode(output, incoming='utf-8').split(os.linesep)


def source_env(env_file):
    p = subprocess.Popen(". %s; env" % env_file, stdout=subprocess.PIPE,
                         shell=True)
    output = p.communicate()[0]

    # sometimes output type would be binary_type, and it don't have splitlines
    # method, so we need to decode
    if isinstance(output, six.binary_type):
        output = encodeutils.safe_decode(output)
    env = dict(line.split('=', 1) for line in output.splitlines() if '=' in line)
    os.environ.update(env)
    return env


def read_json_from_file(path):
    with open(path, 'r') as f:
        j = f.read()
    # don't use jsonutils.load() it conflicts with already decoded input
    return jsonutils.loads(j)


def write_json_to_file(path, data, mode='w'):
    with open(path, mode) as f:
        jsonutils.dump(data, f)


def write_file(path, data, mode='w'):
    with open(path, mode) as f:
        f.write(data)


def parse_ini_file(path):
    parser = configparser.ConfigParser()

    try:
        files = parser.read(path)
    except configparser.MissingSectionHeaderError:
        logger.exception('invalid file type')
        raise
    else:
        if not files:
            raise RuntimeError('file not exist')

    try:
        default = {k: v for k, v in parser.items('DEFAULT')}
    except configparser.NoSectionError:
        default = {}

    config = dict(DEFAULT=default,
                  **{s: {k: v for k, v in parser.items(
                      s)} for s in parser.sections()})

    return config


def get_port_mac(sshclient, port):
    cmd = "ifconfig |grep HWaddr |grep %s |awk '{print $5}' " % port
    status, stdout, stderr = sshclient.execute(cmd)

    if status:
        raise RuntimeError(stderr)
    return stdout.rstrip()


def get_port_ip(sshclient, port):
    cmd = "ifconfig %s |grep 'inet addr' |awk '{print $2}' " \
        "|cut -d ':' -f2 " % port
    status, stdout, stderr = sshclient.execute(cmd)

    if status:
        raise RuntimeError(stderr)
    return stdout.rstrip()


def flatten_dict_key(data):
    next_data = {}

    # use list, because iterable is too generic
    if not any(isinstance(v, (collections.Mapping, list))
               for v in data.values()):
        return data

    for k, v in data.items():
        if isinstance(v, collections.Mapping):
            for n_k, n_v in v.items():
                next_data["%s.%s" % (k, n_k)] = n_v
        # use list because iterable is too generic
        elif isinstance(v, collections.Iterable) and not isinstance(v, six.string_types):
            for index, item in enumerate(v):
                next_data["%s%d" % (k, index)] = item
        else:
            next_data[k] = v

    return flatten_dict_key(next_data)


def translate_to_str(obj):
    if isinstance(obj, collections.Mapping):
        return {str(k): translate_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [translate_to_str(ele) for ele in obj]
    elif isinstance(obj, six.text_type):
        return str(obj)
    return obj


def result_handler(status, data):
    result = {
        'status': status,
        'result': data
    }
    return jsonify(result)


def change_obj_to_dict(obj):
    dic = {}
    for k, v in vars(obj).items():
        try:
            vars(v)
        except TypeError:
            dic.update({k: v})
    return dic


def set_dict_value(dic, keys, value):
    return_dic = dic

    for key in keys.split('.'):
        return_dic.setdefault(key, {})
        if key == keys.split('.')[-1]:
            return_dic[key] = value
        else:
            return_dic = return_dic[key]
    return dic


def get_free_port(ip):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        port = random.randint(5000, 10000)
        while s.connect_ex((ip, port)) == 0:
            port = random.randint(5000, 10000)
        return port


def mac_address_to_hex_list(mac):
    octets = ["0x{:02x}".format(int(elem, 16)) for elem in mac.split(':')]
    assert len(octets) == 6 and all(len(octet) == 4 for octet in octets)
    return octets


def safe_ip_address(ip_addr):
    """ get ip address version v6 or v4 """
    try:
        return ipaddress.ip_address(six.text_type(ip_addr))
    except ValueError:
        logging.error("%s is not valid", ip_addr)
        return None


def get_ip_version(ip_addr):
    """ get ip address version v6 or v4 """
    try:
        address = ipaddress.ip_address(six.text_type(ip_addr))
    except ValueError:
        logging.error("%s is not valid", ip_addr)
        return None
    else:
        return address.version


def ip_to_hex(ip_addr, separator=''):
    try:
        address = ipaddress.ip_address(six.text_type(ip_addr))
    except ValueError:
        logging.error("%s is not valid", ip_addr)
        return ip_addr

    if address.version != 4:
        return ip_addr

    if not separator:
        return '{:08x}'.format(int(address))

    return separator.join('{:02x}'.format(octet) for octet in address.packed)


def try_int(s, *args):
    """Convert to integer if possible."""
    try:
        return int(s)
    except (TypeError, ValueError):
        return args[0] if args else s


class SocketTopology(dict):

    @classmethod
    def parse_cpuinfo(cls, cpuinfo):
        socket_map = {}

        lines = cpuinfo.splitlines()

        core_details = []
        core_lines = {}
        for line in lines:
            if line.strip():
                name, value = line.split(":", 1)
                core_lines[name.strip()] = try_int(value.strip())
            else:
                core_details.append(core_lines)
                core_lines = {}

        for core in core_details:
            socket_map.setdefault(core["physical id"], {}).setdefault(
                core["core id"], {})[core["processor"]] = (
                core["processor"], core["core id"], core["physical id"])

        return cls(socket_map)

    def sockets(self):
        return sorted(self.keys())

    def cores(self):
        return sorted(core for cores in self.values() for core in cores)

    def processors(self):
        return sorted(
            proc for cores in self.values() for procs in cores.values() for
            proc in procs)


def config_to_dict(config):
    return {section: dict(config.items(section)) for section in
            config.sections()}


def validate_non_string_sequence(value, default=None, raise_exc=None):
    # NOTE(ralonsoh): refactor this function to check if raise_exc is an
    # Exception. Remove duplicate code, this function is duplicated in this
    # repository.
    if isinstance(value, collections.Sequence) and not isinstance(value, six.string_types):
        return value
    if raise_exc:
        raise raise_exc  # pylint: disable=raising-bad-type
    return default


def join_non_strings(separator, *non_strings):
    try:
        non_strings = validate_non_string_sequence(non_strings[0], raise_exc=RuntimeError)
    except (IndexError, RuntimeError):
        pass
    return str(separator).join(str(non_string) for non_string in non_strings)


def safe_decode_utf8(s):
    """Safe decode a str from UTF"""
    if six.PY3 and isinstance(s, bytes):
        return s.decode('utf-8', 'surrogateescape')
    return s


class ErrorClass(object):

    def __init__(self, *args, **kwargs):
        if 'test' not in kwargs:
            raise RuntimeError

    def __getattr__(self, item):
        raise AttributeError


class Timer(object):
    def __init__(self, timeout=None):
        super(Timer, self).__init__()
        self.start = self.delta = None
        self._timeout = int(timeout) if timeout else None

    def _timeout_handler(self, *args):
        raise exceptions.TimerTimeout(timeout=self._timeout)

    def __enter__(self):
        self.start = datetime.datetime.now()
        if self._timeout:
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self._timeout)
        return self

    def __exit__(self, *_):
        if self._timeout:
            signal.alarm(0)
        self.delta = datetime.datetime.now() - self.start

    def __getattr__(self, item):
        return getattr(self.delta, item)


def read_meminfo(ssh_client):
    """Read "/proc/meminfo" file and parse all keys and values"""

    cpuinfo = six.BytesIO()
    ssh_client.get_file_obj('/proc/meminfo', cpuinfo)
    lines = cpuinfo.getvalue().decode('utf-8')
    matches = re.findall(r"([\w\(\)]+):\s+(\d+)( kB)*", lines)
    output = {}
    for match in matches:
        output[match[0]] = match[1]

    return output


def find_relative_file(path, task_path):
    """
    Find file in one of places: in abs of path or relative to a directory path,
    in this order.

    :param path:
    :param task_path:
    :return str: full path to file
    """
    # fixme: create schema to validate all fields have been provided
    for lookup in [os.path.abspath(path), os.path.join(task_path, path)]:
        try:
            with open(lookup):
                return lookup
        except IOError:
            pass
    raise IOError(errno.ENOENT, 'Unable to find {} file'.format(path))


def open_relative_file(path, task_path):
    try:
        return open(path)
    except IOError as e:
        if e.errno == errno.ENOENT:
            return open(os.path.join(task_path, path))
        raise


def wait_until_true(predicate, timeout=60, sleep=1, exception=None):
    """Wait until callable predicate is evaluated as True

    :param predicate: (func) callable deciding whether waiting should continue
    :param timeout: (int) timeout in seconds how long should function wait
    :param sleep: (int) polling interval for results in seconds
    :param exception: exception instance to raise on timeout. If None is passed
                      (default) then WaitTimeout exception is raised.
    """
    try:
        with Timer(timeout=timeout):
            while not predicate():
                time.sleep(sleep)
    except exceptions.TimerTimeout:
        if exception and issubclass(exception, Exception):
            raise exception  # pylint: disable=raising-bad-type
        raise exceptions.WaitTimeout
