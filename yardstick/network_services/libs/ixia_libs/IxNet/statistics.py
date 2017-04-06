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
import logging

log = logging.getLogger(__name__)


class IxStats():

    def _get_statistics(self, ixNet):
        stats = {}
        ports_stats = {}
        latency = {}
        viewName = "Traffic Item Statistics"
        views = ixNet.getList('/statistics', 'view')
        viewObj = ''
        editedViewName = '::ixNet::OBJ-/statistics/view:\"' + viewName + '\"'
        for view in views:
            if editedViewName == view:
                viewObj = view
                break

        stats.update(
            {"traffic_item":
             ixNet.execute('getColumnValues', viewObj, 'Traffic Item')})
        stats.update(
            {"Tx_Frames":
             ixNet.execute('getColumnValues', viewObj, 'Tx Frames')})
        stats.update(
            {"Rx_Frames":
             ixNet.execute('getColumnValues', viewObj, 'Rx Frames')})
        stats.update(
            {"Tx_Frame_Rate":
             ixNet.execute('getColumnValues', viewObj, 'Tx Frame Rate')})
        stats.update(
            {"Rx_Frame_Rate":
             ixNet.execute('getColumnValues', viewObj, 'Tx Frame Rate')})
        stats.update(
            {"Store-Forward_Avg_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Avg Latency (ns)')})
        stats.update(
            {"Store-Forward_Min_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Min Latency (ns)')})
        stats.update(
            {"Store-Forward_Max_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Max Latency (ns)')})

        viewName = "Port Statistics"
        editedViewName = '::ixNet::OBJ-/statistics/view:\"' + viewName + '\"'
        for view in views:
            if editedViewName == view:
                viewObj = view
                break

        ports_stats.update(
            {"stat_name":
             ixNet.execute('getColumnValues', viewObj, 'Stat Name')})
        ports_stats.update(
            {"Frames_Tx":
             ixNet.execute('getColumnValues', viewObj, 'Frames Tx.')})
        ports_stats.update(
            {"Valid_Frames_Rx":
             ixNet.execute('getColumnValues', viewObj, 'Valid Frames Rx.')})
        ports_stats.update(
            {"Frames_Tx_Rate":
             ixNet.execute('getColumnValues', viewObj, 'Frames Tx. Rate')})
        ports_stats.update(
            {"Valid_Frames_Rx_Rate":
             ixNet.execute('getColumnValues', viewObj,
                           'Valid Frames Rx. Rate')})
        ports_stats.update(
            {"Tx_Rate_Kbps":
             ixNet.execute('getColumnValues', viewObj, 'Tx. Rate (Kbps)')})
        ports_stats.update(
            {"Rx_Rate_Kbps":
             ixNet.execute('getColumnValues', viewObj, 'Rx. Rate (Kbps)')})
        ports_stats.update(
            {"Tx_Rate_Mbps":
             ixNet.execute('getColumnValues', viewObj, 'Tx. Rate (Mbps)')})
        ports_stats.update(
            {"Rx_Rate_Mbps":
             ixNet.execute('getColumnValues', viewObj, 'Rx. Rate (Mbps)')})

        viewName = "Flow Statistics"
        views = ixNet.getList('/statistics', 'view')
        viewObj = ''
        editedViewName = '::ixNet::OBJ-/statistics/view:\"' + viewName + '\"'
        for view in views:
            if editedViewName == view:
                viewObj = view
                break

        latency.update(
            {"Store-Forward_Avg_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Avg Latency (ns)')})
        latency.update(
            {"Store-Forward_Min_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Min Latency (ns)')})
        latency.update(
            {"Store-Forward_Max_latency_ns":
             ixNet.execute('getColumnValues', viewObj,
                           'Store-Forward Max Latency (ns)')})

        stats.update({"latency": latency})

        return stats, ports_stats
