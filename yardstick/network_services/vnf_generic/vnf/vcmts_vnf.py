# Copyright (c) 2019 Viosoft Corporation
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
import os
import yaml

from influxdb import InfluxDBClient

from yardstick.network_services.vnf_generic.vnf.sample_vnf import SetupEnvHelper
from yardstick.common.constants import INFLUXDB_IP, INFLUXDB_PORT
from yardstick.network_services.vnf_generic.vnf.base import GenericVNF
from yardstick.network_services.vnf_generic.vnf.sample_vnf import ScenarioHelper
from yardstick.network_services.vnf_generic.vnf.vnf_ssh_helper import VnfSshHelper
from yardstick.network_services.utils import get_nsb_option


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
        if len(query_result.keys()) == 0:
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
            return self.build_ds_parameters(pod_cfg)
        else:
            return self.build_us_parameters(pod_cfg)

    def run_vcmtsd(self, stream_dir, pod_cfg):
        cmd = self.build_cmd(stream_dir, pod_cfg)
        LOG.debug("Executing %s", cmd)
        self.ssh_helper.send_command(cmd)

    def setup_vnf_environment(self):
        pass


class VcmtsVNF(GenericVNF):

    TG_NAME = 'VcmtsVNF'
    APP_NAME = 'VcmtsVNF'
    RUN_WAIT = 4

    def __init__(self, name, vnfd):
        super(VcmtsVNF, self).__init__(name, vnfd)
        self.name = name
        self.bin_path = get_nsb_option('bin_path', '')
        self.scenario_helper = ScenarioHelper(self.name)
        self.ssh_helper = VnfSshHelper(self.vnfd_helper.mgmt_interface, self.bin_path)

        self.setup_helper = VcmtsdSetupEnvHelper(self.vnfd_helper,
                                                 self.ssh_helper,
                                                 self.scenario_helper)

    def extract_pod_cfg(self, vcmts_pods_cfg, sg_id):
        for pod_cfg in vcmts_pods_cfg:
            if pod_cfg['sg_id'] == sg_id:
                return pod_cfg

    def instantiate(self, scenario_cfg, context_cfg):
        self._update_collectd_options(scenario_cfg, context_cfg)
        self.scenario_helper.scenario_cfg = scenario_cfg
        self.context_cfg = context_cfg

        options = scenario_cfg.get('options', {})

        try:
            self.vcmts_influxdb_ip = options['vcmts_influxdb_ip']
            self.vcmts_influxdb_port = options['vcmts_influxdb_port']
        except KeyError:
            raise KeyError("Missing destination InfluxDB details in scenario" \
                           " section of the task definition file")

        try:
            vcmtsd_values_filepath = options['vcmtsd_values']
        except KeyError:
            raise KeyError("Missing vcmtsd_values key in scenario options" \
                           "section of the task definition file")

        if not os.path.isfile(vcmtsd_values_filepath):
            raise RuntimeError("The vcmtsd_values file path provided " \
                               "does not exists")

        with open(vcmtsd_values_filepath) as stream:
            vcmtsd_values = yaml.load(stream, Loader=yaml.BaseLoader)

        if vcmtsd_values == None:
            raise RuntimeError("Error reading vcmtsd_values file provided (" +
                               vcmtsd_values_filepath + ")")

        vnf_options = options.get(self.name, {})
        sg_id = str(vnf_options['sg_id'])
        stream_dir = vnf_options['stream_dir']

        vcmts_pods_cfg = vcmtsd_values['topology']['vcmts_pods']

        pod_cfg = self.extract_pod_cfg(vcmts_pods_cfg, sg_id)
        if pod_cfg == None:
            raise KeyError("Service group " + sg_id + " not found")

        self.setup_helper.run_vcmtsd(stream_dir, pod_cfg)

    def _update_collectd_options(self, scenario_cfg, context_cfg):
        scenario_options = scenario_cfg.get('options', {})
        generic_options = scenario_options.get('collectd', {})
        scenario_node_options = scenario_options.get(self.name, {})\
            .get('collectd', {})
        context_node_options = context_cfg.get('nodes', {})\
            .get(self.name, {}).get('collectd', {})

        options = generic_options
        self._update_options(options, scenario_node_options)
        self._update_options(options, context_node_options)

        self.setup_helper.collectd_options = options

    def _update_options(self, options, additional_options):
        for k, v in additional_options.items():
            if isinstance(v, dict) and k in options:
                options[k].update(v)
            else:
                options[k] = v

    def wait_for_instantiate(self):
        pass

    def terminate(self):
        pass

    def scale(self, flavor=""):
        pass

    def collect_kpi(self):
        self.influxdb_helper.copy_kpi()
        return {"n/a": "n/a"}

    def start_collect(self):
        self.influxdb_helper = InfluxDBHelper(self.vcmts_influxdb_ip,
                                              self.vcmts_influxdb_port)
        self.influxdb_helper.start()

    def stop_collect(self):
        pass
