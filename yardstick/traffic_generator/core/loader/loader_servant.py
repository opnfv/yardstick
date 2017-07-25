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

"""Loader servant module used by Loader.

Module is inteded to be private to serve only Loader itself, nevertheless
some methods are exposed outside and can be used by any other clients:
- load_modules(self, path, interface)
- load_module(self, path, interface, class_name)
Those method are stateless static members.

"""
import os
from os import sys
import imp
import fnmatch
import logging
from yardstick.traffic_generator.conf import settings


class LoaderServant(object):
    """Class implements basic dynamic import operations.
    """
    _class_name = None
    _path = None
    _interface = None

    def __init__(self, path, class_name, interface):
        """LoaderServant constructor

        Intializes all data needed for import operations.

        Attributes:
            path: path to directory which contains implementations derived from
                    interface.
            class_name: Class name which will be returned in get_class
                        method, if such definition exists in directory
                        represented by path,
            interface: interface type. Every object which doesn't
                        implement this particular interface will be
                        filtered out.
        """
        self._class_name = class_name
        self._path = path
        self._interface = interface

    def get_class(self):
        """Returns class type based on parameters passed in __init__.

        :return: Type of the found class.
            None if class hasn't been found
        """

        return self.load_module(path=self._path,
                                interface=self._interface,
                                class_name=self._class_name)

    def get_classes(self):
        """Returns all classes in path derived from interface

        :return: Dictionary with following data:
            - key: String representing class name,
            - value: Class type.
        """
        return self.load_modules(path=self._path,
                                 interface=self._interface)

    def get_classes_printable(self):
        """Returns all classes derived from _interface found in path

        :return: String - list of classes in printable format.
        """

        out = self.load_modules(path=self._path,
                                interface=self._interface)
        results = []

        # sort modules to produce the same output everytime
        for (name, mod) in sorted(out.items()):
            desc = (mod.__doc__ or 'No description').strip().split('\n')[0]
            results.append((name, desc))

        header = 'Classes derived from: ' + self._interface.__name__
        output = [header + '\n' + '=' * len(header) + '\n']

        for (name, desc) in results:
            output.append('* %-18s%s' % ('%s:' % name, desc))

            output.append('')

        output.append('')

        return '\n'.join(output)

    @staticmethod
    def load_module(path, interface, class_name):
        """Imports everything from given path and returns class type

        This is based on following conditions:
            - Class is derived from interface,
            - Class type name matches class_name.

        :return: Type of the found class.
            None if class hasn't been found
        """

        results = LoaderServant.load_modules(
            path=path, interface=interface)

        if class_name in results:
            logging.info(
                "Class found: " + class_name + ".")
            return results.get(class_name)

        return None

    @staticmethod
    def load_modules(path, interface):
        """Returns dictionary of class name/class type found in path

        This is based on following conditions:
            - classes found under path are derived from interface.
            - class is not interface itself.

        :return: Dictionary with following data:
            - key: String representing class name,
            - value: Class type.
        """
        result = {}

        for _, mod in LoaderServant._load_all_modules(path):
            # find all classes derived from given interface, but suppress
            # interface itself and any abstract class starting with iface name
            gens = dict((k, v) for (k, v) in list(mod.__dict__.items())
                        if isinstance(v, type) and
                        issubclass(v, interface) and
                        not k.startswith(interface.__name__))
            if gens:
                for (genname, gen) in list(gens.items()):
                    result[genname] = gen
        return result

    @staticmethod
    def _load_all_modules(path):
        """Load all modules from ``path`` directory.

        This is based on the design used by OFTest:
            https://github.com/floodlight/oftest/blob/master/oft

        :param path: Path to a folder of modules.

        :return: List of modules in a folder.
        """
        mods = []

        for root, _, filenames in os.walk(path):
            # Iterate over each python file
            for filename in fnmatch.filter(filenames, '[!.]*.py'):
                modname = os.path.splitext(os.path.basename(filename))[0]

                # skip module load if it is excluded by configuration
                if modname in settings.getValue('EXCLUDE_MODULES'):
                    continue

                try:
                    if modname in sys.modules:
                        mod = sys.modules[modname]
                    else:
                        mod = imp.load_module(
                            modname, *imp.find_module(modname, [root]))
                except ImportError:
                    logging.error('Could not import file ' + filename)
                    raise

                mods.append((modname, mod))

        return mods
