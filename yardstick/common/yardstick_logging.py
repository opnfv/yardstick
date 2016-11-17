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


class Logger(object):
    def __init__(self, logger_name):

        super(Logger, self).__init__()
        CI_DEBUG = os.getenv('CI_DEBUG')
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(logging.DEBUG)

        stream_hdlr = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s '
                                      '%(name)s %(filename)s:%(lineno)d '
                                      '%(levelname)s %(message)s')
        stream_hdlr.setFormatter(formatter)
        if CI_DEBUG is not None and CI_DEBUG.lower() == "true":
            stream_hdlr.setLevel(logging.DEBUG)
        else:
            stream_hdlr.setLevel(logging.INFO)
        self.logger.addHandler(stream_hdlr)

        file_hdlr = logging.FileHandler('/var/log/yardstick.log')
        file_hdlr.setFormatter(formatter)
        file_hdlr.setLevel(logging.DEBUG)
        self.logger.addHandler(file_hdlr)

    def getLogger(self):
        return self.logger


def getLogger(name):
    return Logger(name).getLogger()
