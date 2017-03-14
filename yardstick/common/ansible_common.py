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

from __future__ import absolute_import

import cgitb
import collections
import contextlib as cl
import json
import logging
import os
from collections import Mapping, MutableMapping, Iterable, Callable, deque
from functools import partial
from itertools import chain
from subprocess import CalledProcessError, Popen, PIPE
from tempfile import NamedTemporaryFile

import six
import six.moves.configparser as ConfigParser
import yaml
from six import StringIO
from chainmap import ChainMap

from yardstick.common.utils import Timer


cgitb.enable(format="text")

_LOCAL_DEFAULT = object()

LOG = logging.getLogger(__name__)


def overwrite_dict_to_cfg(cfg, cfg_dict):
    for section in cfg_dict:
        # delete then add
        cfg.remove_section(section)
        cfg.add_section(section)
    for section, val in cfg_dict.items():
        if isinstance(val, six.string_types):
            cfg.set(section, val)
        elif isinstance(val, collections.Mapping):
            for k, v in val.items():
                cfg.set(section, k, v)
        else:
            for v in val:
                cfg.set(section, v)


class TempfileContext(object):
    @staticmethod
    def _try_get_filename_from_file(param):
        try:
            if isinstance(param.read, Callable):
                return param.name
        except AttributeError:
            pass
        # return what was given
        return param

    def __init__(self, data, write_func, descriptor, data_types, directory,
                 prefix, suffix, creator):
        super(TempfileContext, self).__init__()
        self.data = data
        self.write_func = write_func
        self.descriptor = descriptor
        self.data_types = data_types
        self.directory = directory
        self.suffix = suffix
        self.creator = creator
        self.data_file = None
        self.prefix = prefix

    def __enter__(self):
        self.data = self._try_get_filename_from_file(self.data)
        if isinstance(self.data, six.string_types):
            # string -> playbook filename directly
            data_filename = self.data
        elif isinstance(self.data, self.data_types):
            # list of playbooks -> put into a temporary playbook file
            if self.prefix:
                self.prefix = self.prefix.rstrip('_')
            data_filename = ''.join([self.prefix, self.suffix])
            if self.directory:
                data_filename = os.path.join(self.directory, data_filename)
            if not os.path.exists(data_filename):
                self.data_file = open(data_filename, 'w+')
            else:
                self.data_file = self.creator()
            self.write_func(self.data_file)
            self.data_file.flush()
            self.data_file.seek(0)
        else:
            # data not passed properly -> error
            LOG.error("%s type not recognized: %s", self.descriptor, self.data)
            raise ValueError("{} type not recognized".format(self.descriptor))

        LOG.debug("%s file : %s", self.descriptor, data_filename)

        return data_filename

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.data_file:
            self.data_file.close()


class CustomTemporaryFile(object):
    DEFAULT_SUFFIX = None
    DEFAULT_DATA_TYPES = None

    def __init__(self, directory, prefix, suffix=_LOCAL_DEFAULT,
                 data_types=_LOCAL_DEFAULT):
        super(CustomTemporaryFile, self).__init__()
        self.directory = directory
        self.prefix = prefix
        if suffix is not _LOCAL_DEFAULT:
            self.suffix = suffix
        else:
            self.suffix = self.DEFAULT_SUFFIX
        if data_types is not _LOCAL_DEFAULT:
            self.data_types = data_types
        else:
            self.data_types = self.DEFAULT_DATA_TYPES
        # must open "w+" so unicode is encoded correctly
        self.creator = partial(NamedTemporaryFile, mode="w+", delete=False,
                               dir=directory,
                               prefix=prefix,
                               suffix=self.suffix)

    def make_context(self, data, write_func, descriptor='data'):
        return TempfileContext(data, write_func, descriptor, self.data_types,
                               self.directory, self.prefix, self.suffix,
                               self.creator)


class ListTemporaryFile(CustomTemporaryFile):
    DEFAULT_DATA_TYPES = (list, tuple)


class MapTemporaryFile(CustomTemporaryFile):
    DEFAULT_DATA_TYPES = dict


class YmlTemporaryFile(ListTemporaryFile):
    DEFAULT_SUFFIX = '.yml'


class IniListTemporaryFile(ListTemporaryFile):
    DEFAULT_SUFFIX = '.ini'


class IniMapTemporaryFile(MapTemporaryFile):
    DEFAULT_SUFFIX = '.ini'


class JsonTemporaryFile(MapTemporaryFile):
    DEFAULT_SUFFIX = '.json'


class FileNameGenerator(object):
    @staticmethod
    def get_generator_from_filename(filename, directory, prefix, middle):
        basename = os.path.splitext(os.path.basename(filename))[0]
        if not basename.startswith(prefix):
            part_list = [prefix, middle, basename]
        elif not middle or middle in basename:
            part_list = [basename]
        else:
            part_list = [middle, basename]
        return FileNameGenerator(directory=directory, part_list=part_list)

    @staticmethod
    def _handle_existing_file(filename):
        if not os.path.exists(filename):
            return filename

        prefix, suffix = os.path.splitext(os.path.basename(filename))
        directory = os.path.dirname(filename)
        if not prefix.endswith('_'):
            prefix += '_'

        temp_file = NamedTemporaryFile(delete=False, dir=directory,
                                       prefix=prefix, suffix=suffix)
        with cl.closing(temp_file):
            return temp_file.name

    def __init__(self, directory, part_list):
        super(FileNameGenerator, self).__init__()
        self.directory = directory
        self.part_list = part_list

    def make(self, extra):
        if not isinstance(extra, Iterable) or isinstance(extra,
                                                         six.string_types):
            extra = (extra,)  # wrap the singleton in an iterable
        return self._handle_existing_file(
            os.path.join(
                self.directory,
                '_'.join(chain(self.part_list, extra))
            )
        )


class AnsibleNodeDict(Mapping):
    def __init__(self, node_class, nodes):
        super(AnsibleNodeDict, self).__init__()
        # create a dict of name, Node instance
        self.node_dict = {k: v for k, v in
                          (node_class(node).get_tuple() for node in
                           nodes)}
        # collect all the node roles
        self.node_roles = set(
            n['role'] for n in six.itervalues(self.node_dict))

    def __repr__(self):
        return repr(self.node_dict)

    def __len__(self):
        return len(self.node_dict)

    def __getitem__(self, item):
        return self.node_dict[item]

    def __iter__(self):
        return iter(self.node_dict)

    def iter_all_of_type(self, node_type, default=_LOCAL_DEFAULT):
        return (node for node in six.itervalues(self) if
                node.is_role(node_type, default))

    def gen_inventory_lines_for_all_of_type(self, node_type,
                                            default=_LOCAL_DEFAULT):
        return [node.gen_inventory_line() for node in
                self.iter_all_of_type(node_type, default)]

    def gen_all_inventory_lines(self):
        return [node.gen_inventory_line() for node in
                six.itervalues(self.node_dict)]

    def gen_inventory_groups(self):
        # lowercase group names
        return {role.lower(): [node['name'] for
                               node in self.iter_all_of_type(role)]
                for role in self.node_roles}


class AnsibleNode(MutableMapping):
    ANSIBLE_NODE_KEY_MAP = {
        u'ansible_host': 'ip',
        u'ansible_user': 'user',
        u'ansible_port': 'ssh_port',
        u'ansible_ssh_pass': 'password',
        u'ansible_ssh_private_key_file': 'key_filename',
    }

    def __init__(self, data=None, **kwargs):
        super(AnsibleNode, self).__init__()
        if isinstance(data, MutableMapping):
            self.data = data
        else:
            self.data = kwargs

    def __repr__(self):
        return 'AnsibleNode<{}>'.format(self.data)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    @property
    def node_key_map(self):
        return self.ANSIBLE_NODE_KEY_MAP

    def get_inventory_params(self):
        node_key_map = self.node_key_map
        # password or key_filename may not be present
        return {inventory_key: self[self_key] for inventory_key, self_key in
                node_key_map.items() if self_key in self}

    def is_role(self, node_type, default=_LOCAL_DEFAULT):
        if default is not _LOCAL_DEFAULT:
            return self.setdefault('role', default) in node_type
        return node_type in self.get('role', set())

    def gen_inventory_line(self):
        inventory_params = self.get_inventory_params()
        # use format to convert ints
        formatted_args = (u"{}={}".format(*entry) for entry in
                          inventory_params.items())
        line = u" ".join(chain([self['name']], formatted_args))
        return line

    def get_tuple(self):
        return self['name'], self

    def __contains__(self, key):
        return self.data.__contains__(key)

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __delitem__(self, key):
        del self.data[key]

    def __getattr__(self, item):
        return getattr(self.data, item)


class AnsibleCommon(object):
    NODE_CLASS = AnsibleNode
    OUTFILE_PREFIX_TEMPLATE = 'ansible_{:02}'

    __DEFAULT_VALUES_MAP = {
        'default_timeout': 1200,
        'counter': 0,
        'prefix': '',
        # default 10 min ansible timeout for non-main calls
        'ansible_timeout': 600,
        'scripts_dest': None,
        '_deploy_dir': _LOCAL_DEFAULT,
    }

    __DEFAULT_CALLABLES_MAP = {
        'test_vars': dict,
        'inventory_dict': dict,
        '_node_dict': dict,
        '_node_info_dict': dict,
    }

    @classmethod
    def _get_defaults(cls):
        # subclasses will override to change defaults using the ChainMap
        # layering
        values_map_deque, defaults_map_deque = cls._get_defaults_map_deques()
        return ChainMap(*values_map_deque), ChainMap(*defaults_map_deque)

    @classmethod
    def _get_defaults_map_deques(cls):
        # deque so we can insert or append easily
        return (deque([cls.__DEFAULT_VALUES_MAP]),
                deque([cls.__DEFAULT_CALLABLES_MAP]))

    def __init__(self, nodes, **kwargs):
        # TODO: add default Heat vars
        super(AnsibleCommon, self).__init__()
        self.nodes = nodes
        self.counter = 0
        self.prefix = ''
        # default 10 min ansible timeout for non-main calls
        self.ansible_timeout = 600
        self.inventory_dict = None
        self.scripts_dest = None
        self._deploy_dir = _LOCAL_DEFAULT
        self._node_dict = None
        self._node_info_dict = None
        self.callable_task = None
        self.test_vars = None
        self.default_timeout = None
        self.reset(**kwargs)

    def reset(self, **kwargs):
        """
        reset all attributes based on various layers of default dicts
        including new default added in subclasses
        """

        default_values_map, default_callables_map = self._get_defaults()
        for name, default_value in list(default_values_map.items()):
            setattr(self, name, kwargs.pop(name, default_value))

        for name, func in list(default_callables_map.items()):
            try:
                value = kwargs.pop(name)
            except KeyError:
                # usually dict()
                value = func()
            setattr(self, name, value)

    def do_install(self, playbook, directory):
        # TODO: how to get openstack nodes from Heat
        self.gen_inventory_ini_dict()
        self.execute_ansible(playbook, directory)

    @property
    def deploy_dir(self):
        if self._deploy_dir is _LOCAL_DEFAULT:
            raise ValueError('Deploy dir must be set before using it')
        return self._deploy_dir

    @deploy_dir.setter
    def deploy_dir(self, value):
        self._deploy_dir = value

    @property
    def node_dict(self):
        if not self._node_dict:
            self._node_dict = AnsibleNodeDict(self.NODE_CLASS, self.nodes)
            LOG.debug("node_dict = \n%s", self._node_dict)
        return self._node_dict

    def gen_inventory_ini_dict(self):
        if self.inventory_dict and isinstance(self.inventory_dict,
                                              MutableMapping):
            return

        node_dict = self.node_dict
        # add all nodes to 'node' group and specify full parameter there
        self.inventory_dict = {
            "nodes": node_dict.gen_all_inventory_lines()
        }
        # place nodes into ansible groups according to their role
        # using just node name
        self.inventory_dict.update(node_dict.gen_inventory_groups())

    @staticmethod
    def ansible_env(directory, log_file):
        # have to overload here in the env because we can't modify local.conf
        ansible_dict = dict(os.environ, **{
            "ANSIBLE_LOG_PATH": os.path.join(directory, log_file),
            "ANSIBLE_LOG_BASE": directory,
            # # required for SSH to work
            # "ANSIBLE_SSH_ARGS": "-o UserKnownHostsFile=/dev/null "
            #                     "-o GSSAPIAuthentication=no "
            #                     "-o PreferredAuthentications=password "
            #                     "-o ControlMaster=auto "
            #                     "-o ControlPersist=60s",
            # "ANSIBLE_HOST_KEY_CHECKING": "False",
            # "ANSIBLE_SSH_PIPELINING": "True",
        })
        return ansible_dict

    def _gen_ansible_playbook_file(self, playbooks, directory, prefix='tmp'):
        # check what is passed in playbooks
        if isinstance(playbooks, (list, tuple)):
            if len(playbooks) == 1:
                # list or tuple with one member -> take it
                playbooks = playbooks[0]
            else:
                playbooks = [{'include': playbook} for playbook in playbooks]
        prefix = '_'.join([self.prefix, prefix, 'playbook'])
        yml_temp_file = YmlTemporaryFile(directory=directory, prefix=prefix)
        write_func = partial(yaml.safe_dump, playbooks,
                             default_flow_style=False,
                             explicit_start=True)
        return yml_temp_file.make_context(playbooks, write_func,
                                          descriptor='playbooks')

    def _gen_ansible_inventory_file(self, directory, prefix='tmp'):
        def write_func(data_file):
            overwrite_dict_to_cfg(inventory_config, self.inventory_dict)
            debug_inventory = StringIO()
            inventory_config.write(debug_inventory)
            LOG.debug("inventory = \n%s", debug_inventory.getvalue())
            inventory_config.write(data_file)

        prefix = '_'.join([self.prefix, prefix, 'inventory'])
        ini_temp_file = IniMapTemporaryFile(directory=directory, prefix=prefix)
        inventory_config = ConfigParser.ConfigParser(allow_no_value=True)
        return ini_temp_file.make_context(self.inventory_dict, write_func,
                                          descriptor='inventory')

    def _gen_ansible_extra_vars(self, extra_vars, directory, prefix='tmp'):
        if not isinstance(extra_vars, MutableMapping):
            extra_vars = self.test_vars
        prefix = '_'.join([self.prefix, prefix, 'extra_vars'])
        # use JSON because Python YAML serializes unicode wierdly
        json_temp_file = JsonTemporaryFile(directory=directory, prefix=prefix)
        write_func = partial(json.dump, extra_vars, indent=4)
        return json_temp_file.make_context(extra_vars, write_func,
                                           descriptor='extra_vars')

    def _gen_log_names(self, directory, prefix, playbook_filename):
        generator = FileNameGenerator.get_generator_from_filename(
            playbook_filename, directory, self.prefix, prefix)
        return generator.make('execute.log'), generator.make(
            'syntax_check.log')

    @staticmethod
    def get_timeout(*timeouts):
        for timeout in timeouts:
            try:
                timeout = float(timeout)
                if timeout > 0:
                    break
            except (TypeError, ValueError):
                pass
        else:
            timeout = 1200.0
        return timeout

    def execute_ansible(self, playbooks, directory, timeout=None,
                        extra_vars=None, ansible_check=False, prefix='tmp',
                        verbose=False):
        # there can be three types of dirs:
        #  log dir: can be anywhere
        #  inventory dir: can be anywhere
        #  playbook dir: use include to point to files in  consts.ANSIBLE_DIR

        if not os.path.isdir(directory):
            raise OSError("Not a directory, %s", directory)
        timeout = self.get_timeout(timeout, self.default_timeout)

        self.counter += 1
        self.prefix = self.OUTFILE_PREFIX_TEMPLATE.format(self.counter)

        playbook_ctx = self._gen_ansible_playbook_file(playbooks, directory,
                                                       prefix)
        inventory_ctx = self._gen_ansible_inventory_file(directory,
                                                         prefix=prefix)
        extra_vars_ctx = self._gen_ansible_extra_vars(extra_vars, directory,
                                                      prefix=prefix)

        with playbook_ctx as playbook_filename, \
                inventory_ctx as inventory_filename, \
                extra_vars_ctx as extra_vars_filename:
            cmd = [
                "ansible-playbook",
                "--syntax-check",
                "-i",
                inventory_filename,
            ]
            if verbose:
                cmd.append('-vvv')
            if extra_vars_filename is not None:
                cmd.extend([
                    "-e",
                    "@{}".format(extra_vars_filename),
                ])
            cmd.append(playbook_filename)

            log_file_main, log_file_checks = self._gen_log_names(
                directory, prefix, playbook_filename)

            exec_args = {
                'cwd': directory,
                'shell': False,
            }

            if ansible_check:
                LOG.debug('log file checks: %s', log_file_checks)
                exec_args.update({
                    'env': self.ansible_env(directory, log_file_checks),
                    # TODO: add timeout support of use subprocess32 backport
                    # 'timeout': timeout / 2,
                })
                with Timer() as timer:
                    proc = Popen(cmd, stdout=PIPE, **exec_args)
                    output, _ = proc.communicate()
                    retcode = proc.wait()
                LOG.debug("exit status = %s", retcode)
                if retcode != 0:
                    raise CalledProcessError(retcode, cmd, output)
                timeout -= timer.total_seconds()

            cmd.remove("--syntax-check")
            LOG.debug('log file main: %s', log_file_main)
            exec_args.update({
                'env': self.ansible_env(directory, log_file_main),
                # TODO: add timeout support of use subprocess32 backport
                # 'timeout': timeout,
            })
            proc = Popen(cmd, stdout=PIPE, **exec_args)
            output, _ = proc.communicate()
            retcode = proc.wait()
            LOG.debug("exit status = %s", retcode)
            if retcode != 0:
                raise CalledProcessError(retcode, cmd, output)
            return output
