##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import logging
import json

from yardstick.dispatcher.base import Base as DispatchBase


class FileDispatcher(DispatchBase):
    """Dispatcher class for recording data to a file.
    """

    __dispatcher_type__ = "File"

    # TODO: make parameters below configurable, currently just hard coded
    # Path of the file to record the data
    file_path = "/tmp/yardstick.out"
    # The max size of the file
    max_bytes = 0
    # The max number of the files to keep
    backup_count = 0

    def __init__(self, conf):
        super(FileDispatcher, self).__init__(conf)
        self.log = None

        # if the directory and path are configured, then log to the file
        if self.file_path:
            dispatcher_logger = logging.Logger('dispatcher.file')
            dispatcher_logger.setLevel(logging.INFO)
            # create rotating file handler which logs result
            rfh = logging.handlers.RotatingFileHandler(
                self.conf.get('file_path', self.file_path),
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf8')

            rfh.setLevel(logging.INFO)
            # Only wanted the data to be saved in the file, not the
            # project root logger.
            dispatcher_logger.propagate = False
            dispatcher_logger.addHandler(rfh)
            self.log = dispatcher_logger

    def record_result_data(self, data):
        if self.log:
            self.log.info(json.dumps(data))
