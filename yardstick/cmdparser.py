##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" Argument parser for yardstick command line tool

"""

import argparse
import logging

from pkg_resources import get_distribution


class CmdParser(argparse.ArgumentParser):
    def __init__(self):
        argparse.ArgumentParser.__init__(self)

        self.output_file_default = "/tmp/yardstick.out"
        self._version = "yardstick version %s " % \
            get_distribution('yardstick').version

        self.__add_arguments()

    def __add_arguments(self):
        self.add_argument("-d", "--debug",
                          help="increase output verbosity to debug",
                          action="store_true")

        self.add_argument("-v", "--verbose",
                          help="increase output verbosity to info",
                          action="store_true")

        self.add_argument("-V", "--version",
                          help="display version",
                          version=self._version,
                          action="version")

        self.add_argument("--keep-deploy",
                          help="keep context deployed in cloud",
                          action="store_true")

        self.add_argument("--parse-only",
                          help="parse the benchmark config file and exit",
                          action="store_true")

        self.add_argument("--output-file",
                          help="file where output is stored, default %s" %
                          self.output_file_default,
                          default=self.output_file_default)

        self.add_argument("taskfile", type=str,
                          help="path to taskfile", nargs=1)

    def parse_args(self):
        args = argparse.ArgumentParser.parse_args(self)

        logger = logging.getLogger('yardstick')

        logger.setLevel(logging.WARNING)
        if args.verbose:
            logger.setLevel(logging.INFO)
        if args.debug:
            logger.setLevel(logging.DEBUG)

        return args
