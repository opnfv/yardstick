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

# yardstick comment: this is a modified copy of rally/rally/common/utils.py

from __future__ import absolute_import
from __future__ import print_function

import errno
import logging
import os
import subprocess
import sys
from functools import reduce

import yaml
from six.moves import configparser
from oslo_utils import importutils
from oslo_serialization import jsonutils

import yardstick

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


def try_append_module(name, modules):
    if name not in modules:
        modules[name] = importutils.import_module(name)


def import_modules_from_package(package):
    """Import modules from package and append into sys.modules

    :param: package - Full package name. For example: rally.deploy.engines
    """
    path = [os.path.dirname(yardstick.__file__), ".."] + package.split(".")
    path = os.path.join(*path)
    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.startswith("__") or not filename.endswith(".py"):
                continue
            new_package = ".".join(root.split(os.sep)).split("....")[1]
            module_name = "%s.%s" % (new_package, filename[:-3])
            try:
                try_append_module(module_name, sys.modules)
            except ImportError:
                logger.exception("unable to import %s", module_name)


def parse_yaml(file_path):
    try:
        with open(file_path) as f:
            value = yaml.safe_load(f)
    except IOError:
        return {}
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    else:
        return value


def get_param(key, default=''):

    conf_file = os.environ.get('CONF_FILE', '/etc/yardstick/yardstick.yaml')

    conf = parse_yaml(conf_file)
    try:
        return reduce(lambda a, b: a[b], key.split('.'), conf)
    except KeyError:
        if not default:
            raise
        return default


def makedirs(d):
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def execute_command(cmd):
    exec_msg = "Executing command: '%s'" % cmd
    logger.debug(exec_msg)

    output = subprocess.check_output(cmd.split()).split(os.linesep)

    return output


def source_env(env_file):
    p = subprocess.Popen(". %s; env" % env_file, stdout=subprocess.PIPE,
                         shell=True)
    output = p.communicate()[0]
    env = dict((line.split('=', 1) for line in output.splitlines()))
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
    parser.read(path)

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


def set_dict_value(dic, keys, value):
    return_dic = dic

    for key in keys.split('.'):

        return_dic.setdefault(key, {})
        if key == keys.split('.')[-1]:
            return_dic[key] = value
        else:
            return_dic = return_dic[key]

    return dic
