##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging
import os


LOG_FILE = '/tmp/yardstick.log'
LOG_FORMATTER = ('%(asctime)s '
                 '%(name)s %(filename)s:%(lineno)d '
                 '%(levelname)s %(message)s')


class Logger(object):
    def __init__(self, logger_name):

        super(Logger, self).__init__()
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(LOG_FORMATTER)
        stream_hdlr = logging.StreamHandler()
        stream_hdlr.setFormatter(formatter)
        CI_DEBUG = os.getenv('CI_DEBUG')
        if CI_DEBUG is not None and CI_DEBUG.lower() == "true":
            stream_hdlr.setLevel(logging.DEBUG)
        else:
            stream_hdlr.setLevel(logging.INFO)

        file_hdlr = logging.FileHandler(LOG_FILE)
        file_hdlr.setFormatter(formatter)
        file_hdlr.setLevel(logging.DEBUG)

        self.logger.addHandler(stream_hdlr)
        self.logger.addHandler(file_hdlr)

    def getLogger(self):
        return self.logger


def getLogger(name):
    return Logger(name).getLogger()
