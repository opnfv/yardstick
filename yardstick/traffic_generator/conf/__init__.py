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

"""Settings and configuration handlers.

Settings will be loaded from several .conf files
and any user provided settings file.
"""

# pylint: disable=invalid-name

import copy
import os
import re
import logging
import pprint
import ast
import netaddr

from yardstick.common.constants import YARDSTICK_ROOT_PATH
_LOGGER = logging.getLogger(__name__)

_EXTRA_TEST_PARAMS = ['TUNNEL_TYPE']

# regex to parse configuration macros from *.conf
# it will select all patterns starting with # sign
# and returns macro parameters and step
# examples of valid macros:
#   #VMINDEX
#   #MAC(AA:BB:CC:DD:EE:FF) or #MAC(AA:BB:CC:DD:EE:FF,2)
#   #IP(192.168.1.2) or #IP(192.168.1.2,2)
#   #EVAL(2*#VMINDEX)
_PARSE_PATTERN = r'(#[A-Z]+)(\(([^(),]+)(,([0-9]+))?\))?'

class Settings(object):
    """Holding class for settings.
    """
    def __init__(self):
        pass

    def _eval_param(self, param):
        # pylint: disable=invalid-name
        """ Helper function for expansion of references to vsperf parameters
        """
        if isinstance(param, str):
            # evaluate every #PARAM reference inside parameter itself
            macros = re.findall(r'#PARAM\((([\w\-]+)(\[[\w\[\]\-\'\"]+\])*)\)', param)
            if macros:
                for macro in macros:
                    # pylint: disable=eval-used
                    try:
                        tmp_val = str(eval("self.getValue('{}'){}".format(macro[1], macro[2])))
                        param = param.replace('#PARAM({})'.format(macro[0]), tmp_val)
                    # silently ignore that option required by PARAM macro can't be evaluated;
                    # It is possible, that referred parameter will be constructed during runtime
                    # and re-read later.
                    except IndexError:
                        pass
                    except AttributeError:
                        pass
            return param
        elif isinstance(param, list) or isinstance(param, tuple):
            tmp_list = []
            for item in param:
                tmp_list.append(self._eval_param(item))
            return tmp_list
        elif isinstance(param, dict):
            tmp_dict = {}
            for (key, value) in param.items():
                tmp_dict[key] = self._eval_param(value)
            return tmp_dict
        else:
            return param

    def getValue(self, attr):
        """Return a settings item value
        """
        if attr in self.__dict__:
            if attr == 'TEST_PARAMS':
                return getattr(self, attr)
            else:
                master_value = getattr(self, attr)
                # Check if parameter value was modified by CLI option
                cli_value = get_test_param(attr, None)
                if cli_value:
                    # TRAFFIC dictionary is not overridden by CLI option
                    # but only updated by specified values
                    if attr == 'TRAFFIC':
                        tmp_value = copy.deepcopy(master_value)
                        tmp_value = merge_spec(tmp_value, cli_value)
                        return self._eval_param(tmp_value)
                    else:
                        return self._eval_param(cli_value)
                else:
                    return self._eval_param(master_value)
        else:
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, attr))

    def __setattr__(self, name, value):
        """Set a value
        """
        # skip non-settings. this should exclude built-ins amongst others
        if not name.isupper():
            return

        # we can assume all uppercase keys are valid settings
        super(Settings, self).__setattr__(name, value)

    def setValue(self, name, value):
        """Set a value
        """
        if name is not None and value is not None:
            super(Settings, self).__setattr__(name, value)

    def load_from_file(self, path):
        """Update ``settings`` with values found in module at ``path``.
        """
        import imp

        custom_settings = imp.load_source('custom_settings', path)

        for key in dir(custom_settings):
            if getattr(custom_settings, key) is not None:
                setattr(self, key, getattr(custom_settings, key))

    def load_from_dir(self, dir_path):
        """Update ``settings`` with contents of the .conf files at ``path``.

        Each file must be named Nfilename.conf, where N is a single or
        multi-digit decimal number.  The files are loaded in ascending order of
        N - so if a configuration item exists in more that one file the setting
        in the file with the largest value of N takes precedence.

        :param dir_path: The full path to the dir from which to load the .conf
            files.

        :returns: None
        """
        regex = re.compile("^(?P<digit_part>[0-9]+).*.conf$")

        def get_prefix(filename):
            """
            Provide a suitable function for sort's key arg
            """
            match_object = regex.search(os.path.basename(filename))
            return int(match_object.group('digit_part'))

        # get full file path to all files & dirs in dir_path
        file_paths = os.listdir(dir_path)
        print file_paths
        file_paths = [os.path.join(dir_path, x) for x in file_paths]
        print(YARDSTICK_ROOT_PATH)

        # filter to get only those that are a files, with a leading
        # digit and end in '.conf'
        file_paths = [x for x in file_paths if os.path.isfile(x) and
                      regex.search(os.path.basename(x))]

        # sort ascending on the leading digits
        file_paths.sort(key=get_prefix)

        # load settings from each file in turn
        for filepath in file_paths:
            self.load_from_file(filepath)

    def load_from_dict(self, conf):
        """
        Update ``settings`` with values found in ``conf``.

        Unlike the other loaders, this is case insensitive.
        """
        for key in conf:
            if conf[key] is not None:
                if isinstance(conf[key], dict):
                    # recursively update dict items, e.g. TEST_PARAMS
                    setattr(self, key.upper(),
                            merge_spec(getattr(self, key.upper()), conf[key]))
                else:
                    setattr(self, key.upper(), conf[key])

    def load_from_env(self):
        """
        Update ``settings`` with values found in the environment.
        """
        for key in os.environ:
            setattr(self, key, os.environ[key])

    def check_test_params(self):
        """
        Check all parameters defined inside TEST_PARAMS for their
        existence. In case that non existing vsperf parmeter name
        is detected, then VSPER will raise a runtime error.
        """
        unknown_keys = []
        for key in settings.getValue('TEST_PARAMS'):
            if key == 'TEST_PARAMS':
                raise RuntimeError('It is not allowed to define TEST_PARAMS '
                                   'as a test parameter')
            if key not in self.__dict__ and key not in _EXTRA_TEST_PARAMS:
                unknown_keys.append(key)

        if len(unknown_keys):
            raise RuntimeError('Test parameters contain unknown configuration '
                               'parameter(s): {}'.format(', '.join(unknown_keys)))

    def check_vm_settings(self, vm_number):
        """
        Check all VM related settings starting with GUEST_ prefix.
        If it is not available for defined number of VMs, then vsperf
        will try to expand it automatically. Expansion is performed
        also in case that first list item contains a macro.
        """
        for key in self.__dict__:
            if key.startswith('GUEST_'):
                value = self.getValue(key)
                if isinstance(value, str) and str(value).find('#') >= 0:
                    self._expand_vm_settings(key, 1)

                if isinstance(value, list):
                    if len(value) < vm_number or str(value[0]).find('#') >= 0:
                        # expand configuration for all VMs
                        self._expand_vm_settings(key, vm_number)

    def _expand_vm_settings(self, key, vm_number):
        """
        Expand VM option with given key for given number of VMs
        """
        tmp_value = self.getValue(key)
        if isinstance(tmp_value, str):
            scalar = True
            master_value = tmp_value
            tmp_value = [tmp_value]
        else:
            scalar = False
            master_value = tmp_value[0]

        master_value_str = str(master_value)
        if master_value_str.find('#') >= 0:
            self.__dict__[key] = []
            for vmindex in range(vm_number):
                value = master_value_str.replace('#VMINDEX', str(vmindex))
                for macro, args, param, _, step in re.findall(_PARSE_PATTERN, value):
                    multi = int(step) if len(step) and int(step) else 1
                    if macro == '#EVAL':
                        # pylint: disable=eval-used
                        tmp_result = str(eval(param))
                    elif macro == '#MAC':
                        mac_value = netaddr.EUI(param).value
                        mac = netaddr.EUI(mac_value + vmindex * multi)
                        mac.dialect = netaddr.mac_unix_expanded
                        tmp_result = str(mac)
                    elif macro == '#IP':
                        ip_value = netaddr.IPAddress(param).value
                        tmp_result = str(netaddr.IPAddress(ip_value + vmindex * multi))
                    else:
                        raise RuntimeError('Unknown configuration macro {} in {}'.format(macro, key))

                    value = value.replace("{}{}".format(macro, args), tmp_result)

                # retype value to original type if needed
                if not isinstance(master_value, str):
                    value = ast.literal_eval(value)
                self.__dict__[key].append(value)
        else:
            for vmindex in range(len(tmp_value), vm_number):
                self.__dict__[key].append(master_value)

        if scalar:
            self.__dict__[key] = self.__dict__[key][0]

        _LOGGER.debug("Expanding option: %s = %s", key, self.__dict__[key])

    def __str__(self):
        """Provide settings as a human-readable string.

        This can be useful for debug.

        Returns:
            A human-readable string.
        """
        tmp_dict = {}
        for key in self.__dict__:
            tmp_dict[key] = self.getValue(key)

        return pprint.pformat(tmp_dict)

    #
    # validation methods used by step driven testcases
    #
    def validate_getValue(self, result, attr):
        """Verifies, that correct value was returned
        """
        # getValue must be called to expand macros and apply
        # values from TEST_PARAM option
        assert result == self.getValue(attr)
        return True

    def validate_setValue(self, dummy_result, name, value):
        """Verifies, that value was correctly set
        """
        assert value == self.__dict__[name]
        return True

settings = Settings()

def get_test_param(key, default=None):
    """Retrieve value for test param ``key`` if available.

    :param key: Key to retrieve from test params.
    :param default: Default to return if key not found.

    :returns: Value for ``key`` if found, else ``default``.
    """
    test_params = settings.getValue('TEST_PARAMS')
    return test_params.get(key, default) if test_params else default

def merge_spec(orig, new):
    """Merges ``new`` dict with ``orig`` dict, and returns orig.

    This takes into account nested dictionaries. Example:

        >>> old = {'foo': 1, 'bar': {'foo': 2, 'bar': 3}}
        >>> new = {'foo': 6, 'bar': {'foo': 7}}
        >>> merge_spec(old, new)
        {'foo': 6, 'bar': {'foo': 7, 'bar': 3}}

    You'll notice that ``bar.bar`` is not removed. This is the desired result.
    """
    for key in orig:
        if key not in new:
            continue

        # Not allowing derived dictionary types for now
        # pylint: disable=unidiomatic-typecheck
        if type(orig[key]) == dict:
            orig[key] = merge_spec(orig[key], new[key])
        else:
            orig[key] = new[key]

    for key in new:
        if key not in orig:
            orig[key] = new[key]

    return orig
