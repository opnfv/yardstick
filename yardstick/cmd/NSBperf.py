#!/usr/bin/env python
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


"""NSBPERF main script.
"""

from __future__ import absolute_import
from __future__ import print_function
import os
import argparse
import json
import subprocess
import signal
from oslo_serialization import jsonutils

from six.moves import input

CLI_PATH = os.path.dirname(os.path.realpath(__file__))
REPO_PATH = os.path.abspath(os.path.join(CLI_PATH, os.pardir))


def sigint_handler(*args, **kwargs):
    """ Capture ctrl+c and exit cli """
    subprocess.call(["pkill", "-9", "yardstick"])
    raise SystemExit(1)


class YardstickNSCli(object):
    """ This class handles yardstick network serivce testing """

    def __init__(self):
        super(YardstickNSCli, self).__init__()

    @classmethod
    def validate_input(cls, choice, choice_len):
        """ Validate user inputs """
        if not str(choice):
            return 1

        choice = int(choice)
        if not 1 <= choice <= choice_len:
            print("\nInvalid wrong choice...")
            input("Press Enter to continue...")
            return 1
        subprocess.call(['clear'])
        return 0

    @classmethod
    def parse_arguments(cls):
        """
        Parse command line arguments.
        """
        parser = \
            argparse.ArgumentParser(
                prog=__file__,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--version', action='version',
                            version='%(prog)s 0.1')
        parser.add_argument('--list', '--list-tests', action='store_true',
                            help='list all tests and exit')
        parser.add_argument('--list-vnfs', action='store_true',
                            help='list all system vnfs and exit')

        group = parser.add_argument_group('test selection options')
        group.add_argument('--vnf', help='vnf to use')
        group.add_argument('--test', help='test in use')

        args = vars(parser.parse_args())

        return args

    @classmethod
    def generate_kpi_results(cls, tkey, tgen):
        """ Generate report for vnf & traffic generator kpis """
        if tgen:
            print("\n%s stats" % tkey)
            print("----------------------------")
            for key, value in tgen.items():
                if key != "collect_stats":
                    print(json.dumps({key: value}, indent=2))

    @classmethod
    def generate_nfvi_results(cls, nfvi):
        """ Generate report for vnf & traffic generator kpis """
        if nfvi:
            nfvi_kpi = {k: v for k, v in nfvi.items() if k == 'collect_stats'}
            if nfvi_kpi:
                print("\nNFVi stats")
                print("----------------------------")
                for key, value in nfvi_kpi.items():
                    print(json.dumps({key: value}, indent=2))

    def generate_final_report(self, test_case):
        """ Function will check if partial test results are available
        and generates final report in rst format.
        """

        tc_name = os.path.splitext(test_case)[0]
        report_caption = '{}\n{} ({})\n{}\n\n'.format(
            '================================================================',
            'Performance report for', tc_name.upper(),
            '================================================================')
        print(report_caption)
        if os.path.isfile("/tmp/yardstick.out"):
            lines = []
            with open("/tmp/yardstick.out") as infile:
                lines = jsonutils.load(infile)

            if lines:
                lines = \
                    lines['result']["testcases"][tc_name]["tc_data"]
                tc_res = lines.pop(len(lines) - 1)
                for key, value in tc_res["data"].items():
                    self.generate_kpi_results(key, value)
                    self.generate_nfvi_results(value)

    @classmethod
    def handle_list_options(cls, args, test_path):
        """ Process --list cli arguments if needed

        :param args: A dictionary with all CLI arguments
        """
        if args['list_vnfs']:
            vnfs = os.listdir(test_path)
            print("VNF :")
            print("================")
            for index, vnf in enumerate(vnfs, 1):
                print((' %-2s %s' % ('%s:' % str(index), vnf)))
            raise SystemExit(0)

        if args['list']:
            vnfs = os.listdir(test_path)

            print("Available Tests:")
            print("*****************")
            for vnf in vnfs:
                testcases = os.listdir(test_path + vnf)
                print(("VNF :(%s)" % vnf))
                print("================")
                for testcase in [tc for tc in testcases if "tc_" in tc]:
                    print('%s' % testcase)
                print(os.linesep)
            raise SystemExit(0)

    @classmethod
    def terminate_if_less_options(cls, args):
        """ terminate cli if cmdline options is invalid """
        if not (args["vnf"] and args["test"]):
            print("CLI needs option, make sure to pass vnf, test")
            print("eg: NSBperf.py --vnf <vnf untertest> --test <test yaml>")
            raise SystemExit(1)

    def run_test(self, args, test_path):
        """ run requested test """
        try:
            vnf = args.get("vnf", "")
            test = args.get("test", "")

            vnf_dir = test_path + os.sep + vnf
            if not os.path.exists(vnf_dir):
                raise ValueError("'%s', vnf not supported." % vnf)

            testcases = [tc for tc in os.listdir(vnf_dir) if "tc" in tc]
            subtest = set([test]).issubset(testcases)
            if not subtest:
                raise ValueError("'%s', testcase not supported." % test)

            os.chdir(vnf_dir)
            # fixme: Use REST APIs to initiate testcases
            subprocess.check_output(["yardstick", "--debug",
                                     "task", "start", test])
            self.generate_final_report(test)
        except (IOError, ValueError):
            print("Value/I/O error...")
        except BaseException:
            print("Test failed. Please verify test inputs & re-run the test..")
            print("eg: NSBperf.py --vnf <vnf untertest> --test <test yaml>")

    def main(self):
        """Main function.
        """
        test_path = os.path.join(REPO_PATH, "../samples/vnf_samples/nsut/")
        os.chdir(os.path.join(REPO_PATH, "../"))
        args = self.parse_arguments()

        # if required, handle list-* operations
        self.handle_list_options(args, test_path)

        # check for input params
        self.terminate_if_less_options(args)

        # run test
        self.run_test(args, test_path)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    NS_CLI = YardstickNSCli()
    NS_CLI.main()
