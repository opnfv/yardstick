# Copyright 2013 IBM Corp
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# yardstick comment: this is a modified copy of
# ceilometer/ceilometer/dispatcher/file.py

import logging
import json

from oslo_config import cfg

from yardstick.dispatcher.base import Base as DispatchBase

CONF = cfg.CONF
OPTS = [
    cfg.StrOpt('file_path',
               default='/tmp/yardstick.out',
               help='Name and the location of the file to record '
                    'data.'),
    cfg.IntOpt('max_bytes',
               default=0,
               help='The max size of the file.'),
    cfg.IntOpt('backup_count',
               default=0,
               help='The max number of the files to keep.'),
]
CONF.register_opts(OPTS, group="dispatcher_file")


class FileDispatcher(DispatchBase):
    """Dispatcher class for recording data to a file.
    """

    __dispatcher_type__ = "File"

    def __init__(self, conf):
        super(FileDispatcher, self).__init__(conf)
        self.log = None

        # if the directory and path are configured, then log to the file
        if CONF.dispatcher_file.file_path:
            dispatcher_logger = logging.Logger('dispatcher.file')
            dispatcher_logger.setLevel(logging.INFO)
            # create rotating file handler which logs result
            rfh = logging.handlers.RotatingFileHandler(
                self.conf.get('file_path', CONF.dispatcher_file.file_path),
                maxBytes=CONF.dispatcher_file.max_bytes,
                backupCount=CONF.dispatcher_file.backup_count,
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

    def flush_result_data(self):
        pass
