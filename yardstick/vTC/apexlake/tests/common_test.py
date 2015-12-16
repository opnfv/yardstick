__author__ = 'vmricco'

import unittest
import mock
import os
import logging
import ConfigParser
import experimental_framework.common as common
import experimental_framework.constants.conf_file_sections as cf


def reset_common():
    common.LOG = None
    common.CONF_FILE = None
    common.DEPLOYMENT_UNIT = None
    common.ITERATIONS = None
    common.BASE_DIR = None
    common.RESULT_DIR = None
    common.TEMPLATE_DIR = None
    common.TEMPLATE_NAME = None
    common.TEMPLATE_FILE_EXTENSION = None
    common.PKTGEN = None
    common.PKTGEN_DIR = None
    common.PKTGEN_DPDK_DIRECTORY = None
    common.PKTGEN_PROGRAM = None
    common.PKTGEN_COREMASK = None
    common.PKTGEN_MEMCHANNEL = None
    common.PKTGEN_BUS_SLOT_NIC_1 = None
    common.PKTGEN_BUS_SLOT_NIC_2 = None
    common.INFLUXDB_IP = None
    common.INFLUXDB_PORT = None
    common.INFLUXDB_DB_NAME = None


class DummyConfigurationFile(common.ConfigurationFile):
    def __init__(self, sections):
        pass

    def get_variable(self, section, variable_name):
        return 'vTC.yaml'

    def get_variable_list(self, section):
        return ['template_base_name']


class DummyConfigurationFile2(common.ConfigurationFile):
    def __init__(self, sections):
        self.pktgen_counter = 0

    def get_variable(self, section, variable_name):
        if variable_name == cf.CFSG_TEMPLATE_NAME:
            return 'vTC.yaml'
        if variable_name == cf.CFSG_ITERATIONS:
            return 2
        if variable_name == cf.CFSG_DEBUG:
            return True
        if variable_name == cf.CFSP_PACKET_GENERATOR:
            if self.pktgen_counter == 1:
                return 'non_supported'
            self.pktgen_counter += 1
            return 'dpdk_pktgen'
        if variable_name == cf.CFSP_DPDK_PKTGEN_DIRECTORY:
            return os.getcwd()
        if variable_name == cf.CFSP_DPDK_PROGRAM_NAME:
            return 'program'
        if variable_name == cf.CFSP_DPDK_COREMASK:
            return 'coremask'
        if variable_name == cf.CFSP_DPDK_MEMORY_CHANNEL:
            return 'memchannel'
        if variable_name == cf.CFSP_DPDK_BUS_SLOT_NIC_1:
            return 'bus_slot_nic_1'
        if variable_name == cf.CFSP_DPDK_BUS_SLOT_NIC_2:
            return 'bus_slot_nic_2'
        if variable_name == cf.CFSP_DPDK_DPDK_DIRECTORY:
            return os.getcwd()

    def get_variable_list(self, section):
        if section == cf.CFS_PKTGEN:
            return [
                cf.CFSP_DPDK_NAME_IF_2,
                cf.CFSP_DPDK_NAME_IF_1,
                cf.CFSP_DPDK_BUS_SLOT_NIC_1,
                cf.CFSP_DPDK_BUS_SLOT_NIC_2,
                cf.CFSP_DPDK_COREMASK,
                cf.CFSP_DPDK_DPDK_DIRECTORY,
                cf.CFSP_DPDK_PKTGEN_DIRECTORY,
                cf.CFSP_DPDK_MEMORY_CHANNEL,
                cf.CFSP_DPDK_PROGRAM_NAME,
                cf.CFSP_PACKET_GENERATOR
            ]
        else:
            return [
                'template_base_name',
                'iterations',
                cf.CFSG_DEBUG
            ]


class TestCommonInit(unittest.TestCase):

    def setUp(self):
        common.CONF_FILE = DummyConfigurationFile('')
        self.dir = '{}/{}'.format(os.getcwd(),
                                  'experimental_framework/')

    def tearDown(self):
        reset_common()
        # common.CONF_FILE = None

    @mock.patch('os.getcwd')
    @mock.patch('experimental_framework.common.init_conf_file')
    @mock.patch('experimental_framework.common.init_general_vars')
    @mock.patch('experimental_framework.common.init_log')
    @mock.patch('experimental_framework.common.init_pktgen')
    @mock.patch('experimental_framework.common.CONF_FILE')
    def test_init_for_success(self, mock_conf_file, init_pkgen, init_log,
                              init_general_vars, init_conf_file, mock_getcwd):
        mock_getcwd.return_value = self.dir
        common.init(True)
        init_pkgen.assert_called_once()
        init_conf_file.assert_called_once()
        init_general_vars.assert_called_once()
        init_log.assert_called_once()
        expected = self.dir.split('experimental_framework/')[0]
        self.assertEqual(common.BASE_DIR, expected)

    def test_init_general_vars_for_success(self):
        common.BASE_DIR = "{}/".format(os.getcwd())
        common.init_general_vars()
        self.assertEqual(common.TEMPLATE_FILE_EXTENSION, '.yaml')
        heat_dir = self.dir.split('experimental_framework/')[0]
        self.assertEqual(common.TEMPLATE_DIR,
                         '{}{}'.format(heat_dir, 'heat_templates/'))
        self.assertEqual(common.TEMPLATE_NAME, 'vTC.yaml')
        self.assertEqual(common.RESULT_DIR,
                         '{}{}'.format(heat_dir, 'results/'))
        self.assertEqual(common.ITERATIONS, 1)


class TestCommonInit2(unittest.TestCase):

    def setUp(self):
        common.CONF_FILE = DummyConfigurationFile2('')
        self.dir = '{}/{}'.format(os.getcwd(), 'experimental_framework/')

    def tearDown(self):
        reset_common()
        common.CONF_FILE = None

    def test_init_general_vars_2_for_success(self):
        common.BASE_DIR = "{}/".format(os.getcwd())
        common.init_general_vars()
        self.assertEqual(common.TEMPLATE_FILE_EXTENSION, '.yaml')
        heat_dir = self.dir.split('experimental_framework/')[0]
        self.assertEqual(common.TEMPLATE_DIR,
                         '{}{}'.format(heat_dir, 'heat_templates/'))
        self.assertEqual(common.TEMPLATE_NAME, 'vTC.yaml')
        self.assertEqual(common.RESULT_DIR,
                         '{}{}'.format(heat_dir, 'results/'))
        self.assertEqual(common.ITERATIONS, 2)

    def test_init_log_2_for_success(self):
        common.init_log()
        self.assertIsInstance(common.LOG, logging.RootLogger)

    def test_init_pktgen_for_success(self):
        common.init_pktgen()
        self.assertEqual(common.PKTGEN, 'dpdk_pktgen')
        directory = self.dir.split('experimental_framework/')[0]
        self.assertEqual(common.PKTGEN_DIR, directory)
        self.assertEqual(common.PKTGEN_PROGRAM, 'program')
        self.assertEqual(common.PKTGEN_COREMASK, 'coremask')
        self.assertEqual(common.PKTGEN_MEMCHANNEL, 'memchannel')
        self.assertEqual(common.PKTGEN_BUS_SLOT_NIC_1, 'bus_slot_nic_1')
        self.assertEqual(common.PKTGEN_BUS_SLOT_NIC_2, 'bus_slot_nic_2')
        expected_dir = "{}/".format(os.getcwd())
        self.assertEqual(common.PKTGEN_DPDK_DIRECTORY, expected_dir)

    def test_init_pktgen_for_failure(self):
        common.CONF_FILE.get_variable('', cf.CFSP_PACKET_GENERATOR)
        self.assertRaises(ValueError, common.init_pktgen)


class TestConfFileInitialization(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        reset_common()

    @mock.patch('experimental_framework.common.ConfigurationFile',
                side_effect=DummyConfigurationFile)
    def test_init_conf_file_for_success(self, conf_file):
        common.CONF_FILE = None
        common.init_conf_file(False)
        self.assertIsInstance(common.CONF_FILE,
                              DummyConfigurationFile)

        common.CONF_FILE = None
        common.init_conf_file(True)
        self.assertIsInstance(common.CONF_FILE,
                              DummyConfigurationFile)

    @mock.patch('experimental_framework.common.CONF_FILE')
    def test_init_log_for_success(self, mock_conf_file):
        mock_conf_file.get_variable_list.return_value = 'value'
        common.init_log()
        self.assertIsInstance(common.LOG, logging.RootLogger)

    @mock.patch('experimental_framework.common.CONF_FILE')
    def test_init_influxdb_for_success(self, mock_conf_file):
        mock_conf_file.get_variable.return_value = 'value'
        common.init_influxdb()
        self.assertEqual(common.INFLUXDB_IP, 'value')
        self.assertEqual(common.INFLUXDB_PORT, 'value')
        self.assertEqual(common.INFLUXDB_DB_NAME, 'value')


class DummyConfigurationFile3(common.ConfigurationFile):
    counter = 0

    def __init__(self, sections, config_file='conf.cfg'):
        common.ConfigurationFile.__init__(self, sections, config_file)

    @staticmethod
    def _config_section_map(section, config_file, get_counter=None):
        if get_counter:
            return DummyConfigurationFile3.counter
        else:
            DummyConfigurationFile3.counter += 1
            return dict()


class TestConfigFileClass(unittest.TestCase):

    def setUp(self):
        self.sections = [
            'General',
            'OpenStack',
            'Experiment-VNF',
            'PacketGen',
            'Deployment-parameters',
            'Testcase-parameters'
        ]
        c_file = '/tests/data/common/conf.cfg'
        common.BASE_DIR = os.getcwd()
        self.conf_file = common.ConfigurationFile(self.sections, c_file)

    def tearDown(self):
        reset_common()
        common.BASE_DIR = None

    @mock.patch('experimental_framework.common.ConfigurationFile.'
                '_config_section_map',
                side_effect=DummyConfigurationFile3._config_section_map)
    def test___init___for_success(self, mock_conf_map):
        sections = ['General', 'OpenStack', 'Experiment-VNF', 'PacketGen',
                    'Deployment-parameters', 'Testcase-parameters']
        c = DummyConfigurationFile3(
            sections, config_file='/tests/data/common/conf.cfg')
        self.assertEqual(
            DummyConfigurationFile3._config_section_map('', '', True),
            6)
        for section in sections:
            self.assertEqual(getattr(c, section), dict())

    def test__config_section_map_for_success(self):
        general_section = 'General'
        # openstack_section = 'OpenStack'
        config_file = 'tests/data/common/conf.cfg'
        config = ConfigParser.ConfigParser()
        config.read(config_file)

        expected = {
            'benchmarks': 'b_marks',
            'iterations': '1',
            'template_base_name': 't_name'
        }
        output = common.\
            ConfigurationFile._config_section_map(general_section, config)
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.'
                'ConfigurationFile.get_variable_list')
    def test_get_variable_for_success(self, mock_get_var_list):
        section = self.sections[0]
        variable_name = 'template_base_name'
        expected = 't_name'
        mock_get_var_list.return_value = [variable_name]
        output = self.conf_file.get_variable(section, variable_name)
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.'
                'ConfigurationFile.get_variable_list')
    def test_get_variable_for_failure(self, mock_get_var_list):
        section = self.sections[0]
        variable_name = 'something_else'
        self.assertRaises(
            ValueError,
            self.conf_file.get_variable,
            section, variable_name
        )

    def test_get_variable_list_for_success(self):
        section = self.sections[0]
        expected = {
            'benchmarks': 'b_marks',
            'iterations': '1',
            'template_base_name': 't_name'
        }
        output = self.conf_file.get_variable_list(section)
        self.assertEqual(expected, output)

    def test_get_variable_list_for_failure(self):
        section = 'something_else'
        self.assertRaises(
            ValueError,
            self.conf_file.get_variable_list,
            section)


class DummyConfigurationFile4(common.ConfigurationFile):

    def get_variable(self, section, variable_name):
        if variable_name == 'vnic2_type':
            return '"value"'
        elif variable_name == cf.CFSG_BENCHMARKS:
            return "BenchmarkClass1, BenchmarkClass2"
        return '@string "value"'

    # def get_variable_list(self, section):
    #     return list()


class TestCommonMethods(unittest.TestCase):

    def setUp(self):
        self.sections = [
            'General',
            'OpenStack',
            'Experiment-VNF',
            'PacketGen',
            'Deployment-parameters',
            'Testcase-parameters'
        ]
        config_file = '/tests/data/common/conf.cfg'
        common.BASE_DIR = os.getcwd()
        common.CONF_FILE = DummyConfigurationFile4(self.sections, config_file)

    def tearDown(self):
        reset_common()
        common.CONF_FILE = None

    def test_get_credentials_for_success(self):
        expected = {
            'ip_controller': '@string "value"',
            'project': '@string "value"',
            'auth_uri': '@string "value"',
            'user': '@string "value"',
            'heat_url': '@string "value"',
            'password': '@string "value"'
        }
        output = common.get_credentials()
        self.assertEqual(expected, output)

    def test_get_heat_template_params_for_success(self):
        expected = {
            'param_1': '@string "value"',
            'param_2': '@string "value"',
            'param_3': '@string "value"',
            'param_4': '@string "value"'
        }
        output = common.get_heat_template_params()
        self.assertEqual(expected, output)

    def test_get_testcase_params_for_success(self):
        expected = {'test_case_param': '@string "value"'}
        output = common.get_testcase_params()
        self.assertEqual(expected, output)

    def test_get_file_first_line_for_success(self):
        file = 'tests/data/common/conf.cfg'
        expected = '[General]\n'
        output = common.get_file_first_line(file)
        self.assertEqual(expected, output)

    def test_replace_in_file_for_success(self):
        filename = 'tests/data/common/file_replacement.txt'
        text_to_search = 'replacement of'
        text_to_replace = '***'
        common.replace_in_file(filename, text_to_search, text_to_replace)
        after = open(filename, 'r').readline()
        self.assertEqual(after, 'Test for the *** strings into a file\n')
        text_to_search = '***'
        text_to_replace = 'replacement of'
        common.replace_in_file(filename, text_to_search, text_to_replace)

    @mock.patch('os.system')
    @mock.patch('experimental_framework.common.LOG')
    def test_run_command_for_success(self, mock_log, mock_os_system):
        command = 'command to be run'
        common.run_command(command)
        mock_os_system.assert_called_once_with(command)

    @mock.patch('experimental_framework.common.run_command')
    def test_push_data_influxdb_for_success(self, mock_run_cmd):
        data = 'string that describes the data'
        expected = "curl -i -XPOST 'http://None:None/write?db=None' " \
                   "--data-binary string that describes the data"
        common.push_data_influxdb(data)
        mock_run_cmd.assert_called_once_with(expected)

    def test_get_base_dir_for_success(self):
        base_dir = common.BASE_DIR
        common.BASE_DIR = 'base_dir'
        expected = 'base_dir'
        output = common.get_base_dir()
        self.assertEqual(expected, output)
        common.BASE_DIR = base_dir

    def test_get_template_dir_for_success(self):
        template_dir = common.TEMPLATE_DIR
        common.TEMPLATE_DIR = 'base_dir'
        expected = 'base_dir'
        output = common.get_template_dir()
        self.assertEqual(expected, output)
        common.TEMPLATE_DIR = template_dir

    def test_get_dpdk_pktgen_vars_test(self):
        # Test 1
        common.PKTGEN = 'dpdk_pktgen'
        common.PKTGEN_DIR = 'var'
        common.PKTGEN_PROGRAM = 'var'
        common.PKTGEN_COREMASK = 'var'
        common.PKTGEN_MEMCHANNEL = 'var'
        common.PKTGEN_BUS_SLOT_NIC_1 = 'var'
        common.PKTGEN_BUS_SLOT_NIC_2 = 'var'
        common.PKTGEN_DPDK_DIRECTORY = 'var'
        expected = {
            'bus_slot_nic_1': 'var',
            'bus_slot_nic_2': 'var',
            'coremask': 'var',
            'dpdk_directory': 'var',
            'memory_channels': 'var',
            'pktgen_directory': 'var',
            'program_name': 'var'
        }
        output = common.get_dpdk_pktgen_vars()
        self.assertEqual(expected, output)

        # Test 2
        common.PKTGEN = 'something_else'
        common.PKTGEN_DIR = 'var'
        common.PKTGEN_PROGRAM = 'var'
        common.PKTGEN_COREMASK = 'var'
        common.PKTGEN_MEMCHANNEL = 'var'
        common.PKTGEN_BUS_SLOT_NIC_1 = 'var'
        common.PKTGEN_BUS_SLOT_NIC_2 = 'var'
        common.PKTGEN_DPDK_DIRECTORY = 'var'
        expected = {}
        output = common.get_dpdk_pktgen_vars()
        self.assertEqual(expected, output)

    @mock.patch('experimental_framework.common.LOG')
    def test_get_deployment_configuration_variables_for_success(self,
                                                                mock_log):
        expected = {
            'vcpu': ['value'],
            'vnic1_type': ['value'],
            'ram': ['value'],
            'vnic2_type': ['value']
        }
        output = common.get_deployment_configuration_variables_from_conf_file()
        self.assertEqual(expected, output)

    def test_get_benchmarks_from_conf_file_for_success(self):
        expected = ['BenchmarkClass1', 'BenchmarkClass2']
        output = common.get_benchmarks_from_conf_file()
        self.assertEqual(expected, output)


class TestinputValidation(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        reset_common()

    def test_validate_string_for_success(self):
        output = common.InputValidation.validate_string('string', '')
        self.assertTrue(output)

    def test_validate_string_for_failure(self):
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_string,
            list(), ''
        )

    def test_validate_int_for_success(self):
        output = common.InputValidation.validate_integer(1111, '')
        self.assertTrue(output)

    def test_validate_int_for_failure(self):
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_integer,
            list(), ''
        )

    def test_validate_dict_for_success(self):
        output = common.InputValidation.validate_dictionary(dict(), '')
        self.assertTrue(output)

    def test_validate_dict_for_failure(self):
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_dictionary,
            list(), ''
        )

    def test_validate_file_exist_for_success(self):
        filename = 'tests/data/common/file_replacement.txt'
        output = common.InputValidation.validate_file_exist(filename, '')
        self.assertTrue(output)

    def test_validate_file_exist_for_failure(self):
        filename = 'tests/data/common/file_replacement'
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_file_exist,
            filename, ''
        )

    def test_validate_directory_exist_and_format_for_success(self):
        directory = 'tests/data/common/'
        output = common.InputValidation.\
            validate_directory_exist_and_format(directory, '')
        self.assertTrue(output)

    def test_validate_directory_exist_and_format_for_failure(self):
        directory = 'tests/data/com/'
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_directory_exist_and_format,
            directory, ''
        )

    @mock.patch('experimental_framework.common.CONF_FILE')
    def test_validate_configuration_file_parameter_for_success(self,
                                                               mock_conf):
        mock_conf.get_variable_list.return_value = ['param']
        section = ''
        parameter = 'param'
        message = ''
        output = common.InputValidation.\
            validate_configuration_file_parameter(section, parameter, message)
        self.assertTrue(output)

    @mock.patch('experimental_framework.common.CONF_FILE')
    def test_validate_configuration_file_parameter_for_failure(
            self, mock_conf_file):
        section = ''
        parameter = 'something_else'
        message = ''
        mock_conf_file.get_variable_list.return_value(['parameter'])
        self.assertRaises(
            ValueError,
            common.InputValidation.
            validate_configuration_file_parameter,
            section, parameter, message
        )

    def test_validate_configuration_file_section_for_success(self):
        section = 'General'
        message = ''
        output = common.InputValidation.\
            validate_configuration_file_section(section, message)
        self.assertTrue(output)

    def test_validate_configuration_file_section_for_failure(self):
        section = 'Something-Else'
        message = ''
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_configuration_file_section,
            section, message
        )

    def test_validate_boolean_for_success(self):
        message = ''
        boolean = True
        output = common.InputValidation.validate_boolean(boolean, message)
        self.assertTrue(output)

        boolean = 'True'
        output = common.InputValidation.validate_boolean(boolean, message)
        self.assertTrue(output)

        boolean = 'False'
        output = common.InputValidation.validate_boolean(boolean, message)
        self.assertFalse(output)

    def test_validate_boolean_for_failure(self):
        message = ''
        boolean = 'string'
        self.assertRaises(
            ValueError,
            common.InputValidation.validate_boolean,
            boolean, message
        )

    def test_validate_os_credentials_for_failure(self):
        # Test 1
        credentials = list()
        self.assertRaises(ValueError,
                          common.InputValidation.validate_os_credentials,
                          credentials)

        # Test 2
        credentials = dict()
        credentials['ip_controller'] = ''
        credentials['heat_url'] = ''
        credentials['user'] = ''
        credentials['password'] = ''
        credentials['auth_uri'] = ''
        # credentials['project'] = ''
        self.assertRaises(ValueError,
                          common.InputValidation.validate_os_credentials,
                          credentials)

    def test_validate_os_credentials_for_success(self):
        credentials = dict()
        credentials['ip_controller'] = ''
        credentials['heat_url'] = ''
        credentials['user'] = ''
        credentials['password'] = ''
        credentials['auth_uri'] = ''
        credentials['project'] = ''
        self.assertTrue(
            common.InputValidation.validate_os_credentials(credentials))
