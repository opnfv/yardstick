# Copyright (c) 2017 Intel Corporation
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

from oslo_utils import excutils


class ProcessExecutionError(RuntimeError):
    def __init__(self, message, returncode):
        super(ProcessExecutionError, self).__init__(message)
        self.returncode = returncode


class YardstickException(Exception):
    """Base Yardstick Exception.

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    Based on NeutronException class.
    """
    message = "An unknown exception occurred."

    def __init__(self, **kwargs):
        try:
            super(YardstickException, self).__init__(self.message % kwargs)
            self.msg = self.message % kwargs
        except Exception:  # pylint: disable=broad-except
            with excutils.save_and_reraise_exception() as ctxt:
                if not self.use_fatal_exceptions():
                    ctxt.reraise = False
                    # at least get the core message out if something happened
                    super(YardstickException, self).__init__(self.message)

    def __str__(self):
        return self.msg

    def use_fatal_exceptions(self):
        """Is the instance using fatal exceptions.

        :returns: Always returns False.
        """
        return False


class ResourceCommandError(YardstickException):
    message = 'Command: "%(command)s" Failed, stderr: "%(stderr)s"'


class FunctionNotImplemented(YardstickException):
    message = ('The function "%(function_name)s" is not implemented in '
               '"%(class_name)" class.')


class InfluxDBConfigurationMissing(YardstickException):
    message = ('InfluxDB configuration is not available. Add "influxdb" as '
               'a dispatcher and the configuration section')


class YardstickBannedModuleImported(YardstickException):
    # pragma: no cover
    message = 'Module "%(module)s" cannnot be imported. Reason: "%(reason)s"'


class PayloadMissingAttributes(YardstickException):
    message = ('Error instantiating a Payload class, missing attributes: '
               '%(missing_attributes)s')


class HeatTemplateError(YardstickException):
    """Error in Heat during the stack deployment"""
    message = ('Error in Heat during the creation of the OpenStack stack '
               '"%(stack_name)s"')


class IPv6RangeError(YardstickException):
    message = 'Start IP "%(start_ip)s" is greater than end IP "%(end_ip)s"'


class TrafficProfileNotImplemented(YardstickException):
    message = 'No implementation for traffic profile %(profile_class)s.'


class DPDKSetupDriverError(YardstickException):
    message = '"igb_uio" driver is not loaded'


class OVSUnsupportedVersion(YardstickException):
    message = ('Unsupported OVS version "%(ovs_version)s". Please check the '
               'config. OVS to DPDK version map: %(ovs_to_dpdk_map)s.')


class OVSHugepagesInfoError(YardstickException):
    message = 'MemInfo cannnot be retrieved.'


class OVSHugepagesNotConfigured(YardstickException):
    message = 'HugePages are not configured in this system.'


class OVSHugepagesZeroFree(YardstickException):
    message = ('There are no HugePages free in this system. Total HugePages '
               'configured: %(total_hugepages)s')


class OVSDeployError(YardstickException):
    message = 'OVS deploy tool failed with error: %(stderr)s.'


class OVSSetupError(YardstickException):
    message = 'OVS setup error. Command: %(command)s. Error: %(error)s.'


class LibvirtCreateError(YardstickException):
    message = 'Error creating the virtual machine. Error: %(error)s.'


class LibvirtQemuImageBaseImageNotPresent(YardstickException):
    message = ('Error creating the qemu image for %(vm_image)s. Base image: '
               '%(base_image)s. Base image not present in execution host or '
               'remote host.')


class LibvirtQemuImageCreateError(YardstickException):
    message = ('Error creating the qemu image for %(vm_image)s. Base image: '
               '%(base_image)s. Error: %(error)s.')


class ScenarioConfigContextNameNotFound(YardstickException):
    message = 'Context name "%(context_name)s" not found'


class StackCreationInterrupt(YardstickException):
    message = 'Stack create interrupted.'


class TaskRenderArgumentError(YardstickException):
    message = 'Error reading the task input arguments'


class TaskReadError(YardstickException):
    message = 'Failed to read task %(task_file)s'


class TaskRenderError(YardstickException):
    message = 'Failed to render template:\n%(input_task)s'


class TimerTimeout(YardstickException):
    message = 'Timer timeout expired, %(timeout)s seconds'


class WaitTimeout(YardstickException):
    message = 'Wait timeout while waiting for condition'


class ScenarioCreateNetworkError(YardstickException):
    message = 'Create Neutron Network Scenario failed'


class ScenarioCreateSubnetError(YardstickException):
    message = 'Create Neutron Subnet Scenario failed'


class ScenarioDeleteRouterError(YardstickException):
    message = 'Delete Neutron Router Scenario failed'


class MissingPodInfoError(YardstickException):
    message = 'Missing pod args, please check'


class UnsupportedPodFormatError(YardstickException):
    message = 'Failed to load pod info, unsupported format'


class ScenarioCreateRouterError(YardstickException):
    message = 'Create Neutron Router Scenario failed'


class ScenarioRemoveRouterIntError(YardstickException):
    message = 'Remove Neutron Router Interface Scenario failed'


class ScenarioCreateFloatingIPError(YardstickException):
    message = 'Create Neutron Floating IP Scenario failed'


class ScenarioDeleteFloatingIPError(YardstickException):
    message = 'Delete Neutron Floating IP Scenario failed'


class ScenarioCreateSecurityGroupError(YardstickException):
    message = 'Create Neutron Security Group Scenario failed'


class ScenarioDeleteNetworkError(YardstickException):
    message = 'Delete Neutron Network Scenario failed'


class ScenarioCreateServerError(YardstickException):
    message = 'Nova Create Server Scenario failed'


class ScenarioDeleteServerError(YardstickException):
    message = 'Delete Server Scenario failed'


class ScenarioCreateKeypairError(YardstickException):
    message = 'Nova Create Keypair Scenario failed'


class ScenarioDeleteKeypairError(YardstickException):
    message = 'Nova Delete Keypair Scenario failed'


class ScenarioAttachVolumeError(YardstickException):
    message = 'Nova Attach Volume Scenario failed'


class ScenarioGetServerError(YardstickException):
    message = 'Nova Get Server Scenario failed'


class ScenarioGetFlavorError(YardstickException):
    message = 'Nova Get Falvor Scenario failed'


class ScenarioCreateVolumeError(YardstickException):
    message = 'Cinder Create Volume Scenario failed'


class ScenarioDeleteVolumeError(YardstickException):
    message = 'Cinder Delete Volume Scenario failed'


class ScenarioDetachVolumeError(YardstickException):
    message = 'Cinder Detach Volume Scenario failed'


class ApiServerError(YardstickException):
    message = 'An unkown exception happened to Api Server!'


class UploadOpenrcError(ApiServerError):
    message = 'Upload openrc ERROR!'


class UpdateOpenrcError(ApiServerError):
    message = 'Update openrc ERROR!'
