#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" yardstick-plot - a command line tool for visualizing results from the
    output file of yardstick framework.

    Example invocation:
    $ yardstick-plot -i /tmp/yardstick.out -o /tmp/plots/
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import os
import sys
import time

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from oslo_serialization import jsonutils
from six.moves import range
from six.moves import zip


class Parser(object):
    """ Command-line argument and input file parser for yardstick-plot tool"""

    def __init__(self):
        self.data = {
            'ping': [],
            'pktgen': [],
            'iperf3': [],
            'fio': []
        }
        self.default_input_loc = "/tmp/yardstick.out"
        self.scenarios = {}

    def _get_parser(self):
        """get a command-line parser"""
        parser = argparse.ArgumentParser(
            prog='yardstick-plot',
            description="A tool for visualizing results from yardstick. "
                        "Currently supports plotting graphs for output files "
                        "from tests: " + str(list(self.data.keys()))
        )
        parser.add_argument(
            '-i', '--input',
            help="The input file name. If left unspecified then "
                 "it defaults to %s" % self.default_input_loc
        )
        parser.add_argument(
            '-o', '--output-folder',
            help="The output folder location. If left unspecified then "
                 "it defaults to <script_directory>/plots/"
        )
        return parser

    def _add_record(self, record):
        """add record to the relevant scenario"""
        if "runner_id" in record and "benchmark" not in record:
            obj_name = record["scenario_cfg"]["runner"]["object"]
            self.scenarios[record["runner_id"]] = obj_name
            return
        runner_object = self.scenarios[record["runner_id"]]
        for test_type in self.data:
            if test_type in runner_object:
                self.data[test_type].append(record)

    def parse_args(self):
        """parse command-line arguments"""
        parser = self._get_parser()
        self.args = parser.parse_args()
        return self.args

    def parse_input_file(self):
        """parse the input test results file"""
        if self.args.input:
            input_file = self.args.input
        else:
            print(("No input file specified, reading from %s"
                   % self.default_input_loc))
            input_file = self.default_input_loc

        try:
            with open(input_file) as f:
                for line in f:
                    record = jsonutils.loads(line)
                    self._add_record(record)
        except IOError as e:
            print((os.strerror(e.errno)))
            sys.exit(1)


class Plotter(object):
    """Graph plotter for scenario-specific results from yardstick framework"""

    def __init__(self, data, output_folder):
        self.data = data
        self.output_folder = output_folder
        self.fig_counter = 1
        self.colors = ['g', 'b', 'c', 'm', 'y']

    def plot(self):
        """plot the graph(s)"""
        for test_type in self.data.keys():
            if self.data[test_type]:
                plt.figure(self.fig_counter)
                self.fig_counter += 1

                plt.title(test_type, loc="left")
                method_name = "_plot_" + test_type
                getattr(self, method_name)(self.data[test_type])
                self._save_plot(test_type)

    def _save_plot(self, test_type):
        """save the graph to output folder"""
        timestr = time.strftime("%Y%m%d-%H%M%S")
        file_name = test_type + "_" + timestr + ".png"
        if not self.output_folder:
            curr_path = os.path.dirname(os.path.abspath(__file__))
            self.output_folder = os.path.join(curr_path, "plots")
        if not os.path.isdir(self.output_folder):
            os.makedirs(self.output_folder)
        new_file = os.path.join(self.output_folder, file_name)
        plt.savefig(new_file)
        print(("Saved graph to " + new_file))

    def _plot_ping(self, records):
        """ping test result interpretation and visualization on the graph"""
        rtts = [r['benchmark']['data']['rtt'] for r in records]
        seqs = [r['benchmark']['sequence'] for r in records]

        for i in range(0, len(rtts)):
            # If SLA failed
            if not rtts[i]:
                rtts[i] = 0.0
                plt.axvline(seqs[i], color='r')

        # If there is a single data-point then display a bar-chart
        if len(rtts) == 1:
            plt.bar(1, rtts[0], 0.35, color=self.colors[0])
        else:
            plt.plot(seqs, rtts, self.colors[0] + '-')

        self._construct_legend(['rtt'])
        plt.xlabel("sequence number")
        plt.xticks(seqs, seqs)
        plt.ylabel("round trip time in milliseconds (rtt)")

    def _plot_pktgen(self, records):
        """pktgen test result interpretation and visualization on the graph"""
        flows = [r['benchmark']['data']['flows'] for r in records]
        sent = [r['benchmark']['data']['packets_sent'] for r in records]
        received = [int(r['benchmark']['data']['packets_received'])
                    for r in records]

        for i in range(0, len(sent)):
            # If SLA failed
            if not sent[i] or not received[i]:
                sent[i] = 0.0
                received[i] = 0.0
                plt.axvline(flows[i], color='r')

        ppm = [1000000.0 * (i - j) / i for i, j in zip(sent, received)]

        # If there is a single data-point then display a bar-chart
        if len(ppm) == 1:
            plt.bar(1, ppm[0], 0.35, color=self.colors[0])
        else:
            plt.plot(flows, ppm, self.colors[0] + '-')

        self._construct_legend(['ppm'])
        plt.xlabel("number of flows")
        plt.ylabel("lost packets per million packets (ppm)")

    def _plot_iperf3(self, records):
        """iperf3 test result interpretation and visualization on the graph"""
        intervals = []
        for r in records:
            #  If did not fail the SLA
            if r['benchmark']['data']:
                intervals.append(r['benchmark']['data']['intervals'])
            else:
                intervals.append(None)

        kbps = [0]
        seconds = [0]
        for i, val in enumerate(intervals):
            if val:
                for j, _ in enumerate(intervals):
                    kbps.append(val[j]['sum']['bits_per_second'] / 1000)
                    seconds.append(seconds[-1] + val[j]['sum']['seconds'])
            else:
                kbps.append(0.0)
                # Don't know how long the failed test took, add 1 second
                # TODO more accurate solution or replace x-axis from seconds
                # to measurement nr
                seconds.append(seconds[-1] + 1)
                plt.axvline(seconds[-1], color='r')

        self._construct_legend(['bandwidth'])
        plt.plot(seconds[1:], kbps[1:], self.colors[0] + '-')
        plt.xlabel("time in seconds")
        plt.ylabel("bandwidth in Kb/s")

    def _plot_fio(self, records):
        """fio test result interpretation and visualization on the graph"""
        rw_types = [r['sargs']['options']['rw'] for r in records]
        seqs = [x for x in range(1, len(records) + 1)]
        data = {}

        for i in range(0, len(records)):
            is_r_type = rw_types[i] == "read" or rw_types[i] == "randread"
            is_w_type = rw_types[i] == "write" or rw_types[i] == "randwrite"
            is_rw_type = rw_types[i] == "rw" or rw_types[i] == "randrw"

            if is_r_type or is_rw_type:
                # Convert to float
                data['read_lat'] = \
                    [r['benchmark']['data']['read_lat'] for r in records]
                data['read_lat'] = \
                    [float(i) for i in data['read_lat']]
                # Convert to int
                data['read_bw'] = \
                    [r['benchmark']['data']['read_bw'] for r in records]
                data['read_bw'] =  \
                    [int(i) for i in data['read_bw']]
                # Convert to int
                data['read_iops'] = \
                    [r['benchmark']['data']['read_iops'] for r in records]
                data['read_iops'] = \
                    [int(i) for i in data['read_iops']]

            if is_w_type or is_rw_type:
                data['write_lat'] = \
                    [r['benchmark']['data']['write_lat'] for r in records]
                data['write_lat'] = \
                    [float(i) for i in data['write_lat']]

                data['write_bw'] = \
                    [r['benchmark']['data']['write_bw'] for r in records]
                data['write_bw'] = \
                    [int(i) for i in data['write_bw']]

                data['write_iops'] = \
                    [r['benchmark']['data']['write_iops'] for r in records]
                data['write_iops'] = \
                    [int(i) for i in data['write_iops']]

        # Divide the area into 3 subplots, sharing a common x-axis
        fig, axl = plt.subplots(3, sharex=True)
        axl[0].set_title("fio", loc="left")

        self._plot_fio_helper(data, seqs, 'read_bw', self.colors[0], axl[0])
        self._plot_fio_helper(data, seqs, 'write_bw', self.colors[1], axl[0])
        axl[0].set_ylabel("Bandwidth in KB/s")

        self._plot_fio_helper(data, seqs, 'read_iops', self.colors[0], axl[1])
        self._plot_fio_helper(data, seqs, 'write_iops', self.colors[1], axl[1])
        axl[1].set_ylabel("IOPS")

        self._plot_fio_helper(data, seqs, 'read_lat', self.colors[0], axl[2])
        self._plot_fio_helper(data, seqs, 'write_lat', self.colors[1], axl[2])
        axl[2].set_ylabel("Latency in " + u"\u00B5s")

        self._construct_legend(['read', 'write'], obj=axl[0])
        plt.xlabel("Sequence number")
        plt.xticks(seqs, seqs)

    def _plot_fio_helper(self, data, seqs, key, bar_color, axl):
        """check if measurements exist for a key and then plot the
           data to a given subplot"""
        if key in data:
            if len(data[key]) == 1:
                axl.bar(0.1, data[key], 0.35, color=bar_color)
            else:
                line_style = bar_color + '-'
                axl.plot(seqs, data[key], line_style)

    def _construct_legend(self, legend_texts, obj=plt):
        """construct legend for the plot or subplot"""
        ci = 0
        lines = []

        for text in legend_texts:
            line = mlines.Line2D([], [], color=self.colors[ci], label=text)
            lines.append(line)
            ci += 1

        lines.append(mlines.Line2D([], [], color='r', label="SLA failed"))

        getattr(obj, "legend")(
            bbox_to_anchor=(0.25, 1.02, 0.75, .102),
            loc=3,
            borderaxespad=0.0,
            ncol=len(lines),
            mode="expand",
            handles=lines
        )


def main():
    parser = Parser()
    args = parser.parse_args()
    print("Parsing input file")
    parser.parse_input_file()
    print("Initializing plotter")
    plotter = Plotter(parser.data, args.output_folder)
    print("Plotting graph(s)")
    plotter.plot()


if __name__ == '__main__':
    main()
