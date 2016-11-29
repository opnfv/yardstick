##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging
import os
import sys

import yardstick.vTC.apexlake as apexlake

# Hack to be able to run apexlake unit tests
# without having to install apexlake.
sys.path.append(os.path.dirname(apexlake.__file__))

LOG_FILE = '/tmp/yardstick.log'
LOG_FORMATTER = ('%(asctime)s '
                 '%(name)s %(filename)s:%(lineno)d '
                 '%(levelname)s %(message)s')

_LOG_FORMATTER = logging.Formatter(LOG_FORMATTER)
_LOG_STREAM_HDLR = logging.StreamHandler()
_LOG_FILE_HDLR = logging.FileHandler(LOG_FILE)

def _init_logging():

    _LOG_STREAM_HDLR.setFormatter(_LOG_FORMATTER)

    # don't append to log file, clobber
    _LOG_FILE_HDLR.setFormatter(_LOG_FORMATTER)
    _LOG_FILE_HDLR.setLevel(logging.DEBUG)

    del logging.root.handlers[:]
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(_LOG_STREAM_HDLR)
    logging.root.addHandler(_LOG_FILE_HDLR)
    logging.debug("logging.root.handlers = %s", logging.root.handlers)

    CI_DEBUG = os.environ.get('CI_DEBUG')
    if CI_DEBUG is not None and CI_DEBUG.lower() == "true":
        _LOG_STREAM_HDLR.setLevel(logging.DEBUG)
    else:
        _LOG_STREAM_HDLR.setLevel(logging.INFO)
