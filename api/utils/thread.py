##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import threading
import os
import logging

from oslo_serialization import jsonutils

from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


class TaskThread(threading.Thread):

    def __init__(self, target, args, handler):
        super(TaskThread, self).__init__(target=target, args=args)
        self.target = target
        self.args = args
        self.handler = handler

    def run(self):
        if self.handler.__class__.__name__.lower().startswith('v2'):
            self.handler.update_attr(self.args.task_id, {'status': consts.TASK_NOT_DONE})
        else:
            update_data = {'task_id': self.args.task_id, 'status': consts.TASK_NOT_DONE}
            self.handler.insert(update_data)

        LOG.info('Starting run task')
        try:
            data = self.target(self.args)
        except Exception as e:
            LOG.exception('Task Failed')
            update_data = {'status': consts.TASK_FAILED, 'error': str(e)}
            self.handler.update_attr(self.args.task_id, update_data)
        else:
            LOG.info('Task Finished')
            LOG.debug('Result: %s', data)

            if self.handler.__class__.__name__.lower().startswith('v2'):
                new_data = {'status': consts.TASK_DONE, 'result': jsonutils.dumps(data['result'])}
                self.handler.update_attr(self.args.task_id, new_data)
                os.remove(self.args.inputfile[0])
            else:
                data['result'] = jsonutils.dumps(data.get('result', {}))
                self.handler.update_attr(self.args.task_id, data)
