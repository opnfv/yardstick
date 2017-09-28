##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import logging
import os
import errno

LOG_DIR = '/tmp/yardstick'
LOG_FILE = os.path.join(LOG_DIR, 'yardstick.log')
LOG_FORMATTER = '%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d %(message)s'

_LOG_FORMATTER = logging.Formatter(LOG_FORMATTER)
_LOG_STREAM_HDLR = logging.StreamHandler()
_LOG_FILE_HDLR = logging.FileHandler(LOG_FILE)

LOG = logging.getLogger(__name__)
try:
    os.makedirs(LOG_DIR)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

def _init_logging():

    LOG.setLevel(logging.DEBUG)

    _LOG_STREAM_HDLR.setFormatter(_LOG_FORMATTER)
    if os.environ.get('CI_DEBUG', '').lower() in {'1', 'y', "yes", "true"}:
        _LOG_STREAM_HDLR.setLevel(logging.DEBUG)
    else:
        _LOG_STREAM_HDLR.setLevel(logging.INFO)
    # don't append to log file, clobber
    _LOG_FILE_HDLR.setFormatter(_LOG_FORMATTER)
    _LOG_FILE_HDLR.setLevel(logging.DEBUG)

    del logging.root.handlers[:]
    logging.root.addHandler(_LOG_STREAM_HDLR)
    logging.root.addHandler(_LOG_FILE_HDLR)
    logging.debug("logging.root.handlers = %s", logging.root.handlers)
