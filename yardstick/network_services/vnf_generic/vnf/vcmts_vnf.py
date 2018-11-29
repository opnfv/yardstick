# Copyright (c) 2018 Viosoft Corporation
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

import logging
import yaml
import os

from influxdb import InfluxDBClient

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ResourceHelper
from yardstick.network_services.vnf_generic.vnf.sample_vnf import SampleVNF
from yardstick.common.constants import INFLUXDB_IP, INFLUXDB_PORT


LOG = logging.getLogger(__name__)


class InfluxDBHelper(object):

    INITIAL_VALUE = 'now() - 1m'

    def __init__(self, vcmts_influxdb_ip, vcmts_influxdb_port):
        self._vcmts_influxdb_ip = vcmts_influxdb_ip
        self._vcmts_influxdb_port = vcmts_influxdb_port
        self._last_upstream_rx = self.INITIAL_VALUE
        self._last_values_time = dict()

    def start(self):
        self._read_client = InfluxDBClient(host=self._vcmts_influxdb_ip,
                                           port=self._vcmts_influxdb_port,
                                           database='collectd')
        self._write_client = InfluxDBClient(host=INFLUXDB_IP,
                                            port=INFLUXDB_PORT,
                                            database='collectd')

    def _get_last_value_time(self, measurement):
        if measurement in self._last_values_time:
            return self._last_values_time[measurement]
        return self.INITIAL_VALUE

    def _set_last_value_time(self, measurement, time):
        self._last_values_time[measurement] = "'" + time + "'"

    def _query_measurement(self, measurement):
        # There is a delay before influxdb flushes the data
        query = "SELECT * FROM " + measurement + " WHERE time > " \
                + self._get_last_value_time(measurement) \
                + " ORDER BY time ASC;"
        query_result = self._read_client.query(query)
        if len(query_result) == 0:
            return None
        return query_result.get_points(measurement)

    def _rw_measurment(self, measurement, columns):
        query_result = self._query_measurement(measurement)
        if query_result == None:
            return

        points_to_write = list()
        for entry in query_result:
            point = {
                "measurement": measurement,
                "tags": {
                    "type": entry['type'],
                    "host": entry['host']
                },
                "time": entry['time'],
                "fields": {}
            }

            for column in columns:
                if column == 'value':
                    point["fields"][column] = float(entry[column])
                else:
                    point["fields"][column] = entry[column]

            points_to_write.append(point)
            self._set_last_value_time(measurement, entry['time'])

        # Write the points to yardstick database
        if self._write_client.write_points(points_to_write):
            LOG.debug("%d new points written to '%s' measurement",
                      len(points_to_write), measurement)

    def copy_kpi(self):
        self._rw_measurment("cpu_value", ["instance", "type_instance", "value"])
        self._rw_measurment("cpufreq_value", ["type_instance", "value"])
        self._rw_measurment("downstream_rx", ["value"])
        self._rw_measurment("downstream_tx", ["value"])
        self._rw_measurment("downstream_value", ["value"])
        self._rw_measurment("ds_per_cm_value", ["instance", "value"])
        self._rw_measurment("intel_rdt_value", ["instance", "type_instance", "value"])
        self._rw_measurment("turbostat_value", ["instance", "type_instance", "value"])
        self._rw_measurment("upstream_rx", ["value"])
        self._rw_measurment("upstream_tx", ["value"])
        self._rw_measurment("upstream_value", ["value"])


class VcmtsdSetupEnvHelper(SetupEnvHelper):

    BASE_PARAMETERS = "export LD_LIBRARY_PATH=/opt/collectd/lib:;"\
                    + "export CMK_PROC_FS=/host/proc;"

    def __init__(self, vnfd_helper, ssh_helper, scenario_helper):
        super(VcmtsdSetupEnvHelper, self).__init__(vnfd_helper,
                                                   ssh_helper,
                                                   scenario_helper)

    def run_vcmtsd(self):
        LOG.debug("Executing %s", self.cmd)
        self.ssh_helper.send_command(self.cmd)

    def build_us_parameters(self, pod_cfg):
        return self.BASE_PARAMETERS + " " \
             + " /opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --socket-id=" + pod_cfg['cpu_socket_id'] \
             + " --pool=shared" \
             + " /vcmts-config/run_upstream.sh " + pod_cfg['sg_id'] \
             + " " + pod_cfg['ds_core_type'] \
             + " " + pod_cfg['num_ofdm'] + "ofdm" \
             + " " + pod_cfg['num_subs'] + "cm" \
             + " " + pod_cfg['cm_crypto'] \
             + " " + pod_cfg['qat'] \
             + " " + pod_cfg['net_us'] \
             + " " + pod_cfg['power_mgmt']

    def build_ds_parameters(self, pod_cfg):
        return self.BASE_PARAMETERS + " " \
             + " /opt/bin/cmk isolate --conf-dir=/etc/cmk" \
             + " --socket-id=" + pod_cfg['cpu_socket_id'] \
             + " --pool=" + pod_cfg['ds_core_type'] \
             + " /vcmts-config/run_downstream.sh " + pod_cfg['sg_id'] \
             + " " + pod_cfg['ds_core_type'] \
             + " " + pod_cfg['ds_core_pool_index'] \
             + " " + pod_cfg['num_ofdm'] + "ofdm" \
             + " " + pod_cfg['num_subs'] + "cm" \
             + " " + pod_cfg['cm_crypto'] \
             + " " + pod_cfg['qat'] \
             + " " + pod_cfg['net_ds'] \
             + " " + pod_cfg['power_mgmt']

    def build_cmd(self, stream_dir, pod_cfg):
        if stream_dir == 'ds':
            self.cmd = self.build_ds_parameters(pod_cfg)
        else:
            self.cmd = self.build_us_parameters(pod_cfg)

    def setup_vnf_environment(self):
        pass


class VcmtsResourceHelper(ResourceHelper):

    def __init__(self, setup_helper):
        super(VcmtsResourceHelper, self).__init__(setup_helper)

    def setup(self):
        self.resource = self.setup_helper.setup_vnf_environment()

    def start(self):
        self.setup_helper.run_vcmtsd()

class VcmtsVNF(SampleVNF):

    TG_NAME = 'VcmtsVNF'
    APP_NAME = 'VcmtsVNF'
    RUN_WAIT = 4

    def __init__(self, name, vnfd, task_id):
        super(VcmtsVNF, self).__init__(name, vnfd, task_id,
        setup_env_helper_type=VcmtsdSetupEnvHelper,
        resource_helper_type=VcmtsResourceHelper)
        self.name = name

    def read_yaml_file(self, path):
        """Read yaml file"""
        with open(path) as stream:
            data = yaml.load(stream, Loader=yaml.BaseLoader)
            return data

    def extract_pod_cfg(self, vcmts_pods_cfg, sg_id):
        for pod_cfg in vcmts_pods_cfg:
            if pod_cfg['sg_id'] == sg_id:
                return pod_cfg
        LOG.error("Service group %s not found", sg_id)
        return None

    def instantiate(self, scenario_cfg, context_cfg):
        self._update_collectd_options(scenario_cfg, context_cfg)
        options = scenario_cfg['options']
        self.vcmts_influxdb_ip = options['vcmts_influxdb_ip']
        self.vcmts_influxdb_port = options['vcmts_influxdb_port']

        vcmtsd_values_filepath = options['vcmtsd_values']
        if not os.path.isfile(vcmtsd_values_filepath):
            LOG.exception("vcmtsd_values file provided (%s) does not exists",
                          vcmtsd_values_filepath)

        sg_id = str(options[self.name]['sg_id'])
        stream_dir = str(options[self.name]['stream_dir'])

        vcmtsd_values = self.read_yaml_file(vcmtsd_values_filepath)
        vcmts_pods_cfg = vcmtsd_values['topology']['vcmts_pods']

        pod_cfg = self.extract_pod_cfg(vcmts_pods_cfg, sg_id)

        self.setup_helper.build_cmd(stream_dir, pod_cfg)
        self.resource_helper.setup()
        self.resource_helper.start()

    def wait_for_instantiate(self):
        pass

    def terminate(self):
        pass

    def scale(self, flavor=""):
        pass

    def collect_kpi(self):
        self.influxdb_helper.copy_kpi()
        result = {"vcmts_data": "data"}
        return result

    def start_collect(self):
        self.influxdb_helper = InfluxDBHelper(self.vcmts_influxdb_ip,
                                              self.vcmts_influxdb_port)
        self.influxdb_helper.start()

    def stop_collect(self):
        pass
