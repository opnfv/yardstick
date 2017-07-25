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

"""Simple kernel module manager implementation.
"""
import os
import subprocess
import logging

from tools import tasks

class ModuleManager(object):
    """Simple module manager which acts as system wrapper for Kernel Modules.
    """

    _logger = logging.getLogger(__name__)

    def __init__(self):
        """Initializes data
        """
        self._modules = []

    def insert_module(self, module, auto_remove=True):
        """Method inserts given module.

        In case that module name ends with .ko suffix then insmod will
        be used for its insertion. Otherwise modprobe will be called.

        :param module: a name of kernel module
        :param auto_remove: if True (by default), then module will be
            automatically removed by remove_modules() method
        """
        module_base_name = os.path.basename(os.path.splitext(module)[0])

        if self.is_module_inserted(module):
            self._logger.info('Module already loaded \'%s\'.', module_base_name)
            # add it to internal list, so we can try to remove it at the end
            if auto_remove:
                self._modules.append(module)
            return

        try:
            if module.endswith('.ko'):
                # load module dependecies first, but suppress automatic
                # module removal at the end; Just for case, that module
                # depends on generic module
                for depmod in self.get_module_dependecies(module):
                    self.insert_module(depmod, auto_remove=False)

                tasks.run_task(['sudo', 'insmod', module], self._logger,
                               'Insmod module \'%s\'...' % module_base_name, True)
            else:
                tasks.run_task(['sudo', 'modprobe', module], self._logger,
                               'Modprobe module \'%s\'...' % module_base_name, True)
            if auto_remove:
                self._modules.append(module)
        except subprocess.CalledProcessError:
            # in case of error, show full module name
            self._logger.error('Unable to insert module \'%s\'.', module)
            raise  # fail catastrophically

    def insert_modules(self, modules):
        """Method inserts list of modules.

        :param modules: a list of modules to be inserted
        """
        for module in modules:
            self.insert_module(module)

    def remove_module(self, module):
        """Removes a single module.

        :param module: a name of kernel module
        """
        if self.is_module_inserted(module):
            # get module base name, i.e strip path and .ko suffix if possible
            module_base_name = os.path.basename(os.path.splitext(module)[0])

            try:
                self._logger.info('Removing module \'%s\'...', module_base_name)
                subprocess.check_call('sudo rmmod {}'.format(module_base_name),
                                      shell=True, stderr=subprocess.DEVNULL)
                # in case that module was loaded automatically by modprobe
                # to solve dependecies, then it is not in internal list of modules
                if module in self._modules:
                    self._modules.remove(module)
            except subprocess.CalledProcessError:
                # in case of error, show full module name...
                self._logger.info('Unable to remove module \'%s\'.', module)
                # ...and list of dependend modules, if there are any
                module_details = self.get_module_details(module_base_name)
                if module_details:
                    mod_dep = module_details.split(' ')[3].rstrip(',')
                    if mod_dep[0] != '-':
                        self._logger.debug('Module \'%s\' is used by module(s) \'%s\'.',
                                           module_base_name, mod_dep)

    def remove_modules(self):
        """Removes all modules that have been previously inserted.
        """
        # remove modules in reverse order to respect their dependencies
        for module in reversed(self._modules):
            self.remove_module(module)

    def is_module_inserted(self, module):
        """Check if a module is inserted on system.

        :param module: a name of kernel module
        """
        module_base_name = os.path.basename(os.path.splitext(module)[0])

        return self.get_module_details(module_base_name) != None

    @staticmethod
    def get_module_details(module):
        """Return details about given module

        :param module: a name of kernel module
        :returns: In case that module is loaded in OS, then corresponding
            line from /proc/modules will be returned. Otherwise it returns None.
        """
        # get list of modules from kernel
        with open('/proc/modules') as mod_file:
            loaded_mods = mod_file.readlines()

        # check if module is loaded
        for line in loaded_mods:
            # underscores '_' and dashes '-' in module names are interchangeable, so we
            # have to normalize module names before comparision
            if line.split(' ')[0].replace('-', '_') == module.replace('-', '_'):
                return line

        return None

    def get_module_dependecies(self, module):
        """Return list of modules, which must be loaded before module itself

        :param module: a name of kernel module
        :returns: In case that module has any dependencies, then list of module
            names will be returned. Otherwise it returns empty list, i.e. [].
        """
        deps = ''
        try:
            # get list of module dependecies from kernel
            deps = subprocess.check_output('modinfo -F depends {}'.format(module),
                                           shell=True).decode().rstrip('\n')
        except subprocess.CalledProcessError:
            # in case of error, show full module name...
            self._logger.info('Unable to get list of dependecies for module \'%s\'.', module)
            # ...and try to continue, just for case that dependecies are already loaded

        if len(deps):
            return deps.split(',')
        else:
            return []
