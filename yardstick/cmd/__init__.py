##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import sys


def print_hbar(barlen):
    '''print to stdout a horizontal bar'''
    sys.stdout.write("+"),
    for _ in range(barlen):
        sys.stdout.write("-"),
    sys.stdout.write("+\n")
