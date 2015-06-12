#!/usr/bin/env python

##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

""" yardstick - command line tool for managing benchmarks

    Example invocation:
    $ yardstick samples/ping-task.yaml
"""
import sys

from yardstick.cmd.cli import YardstickCLI


def main():
    '''yardstick main'''
    YardstickCLI().main(sys.argv[1:])

if __name__ == '__main__':
    main()
