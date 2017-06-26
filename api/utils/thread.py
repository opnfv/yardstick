import threading
import logging

from oslo_serialization import jsonutils

from api.database.v1.handlers import TasksHandler
from yardstick.common import constants as consts

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class TaskThread(threading.Thread):

    def __init__(self, target, args):
        super(TaskThread, self).__init__(target=target, args=args)
        self.target = target
        self.args = args

    def run(self):
        task_handler = TasksHandler()
        data = {'task_id': self.args.task_id, 'status': consts.TASK_NOT_DONE}
        task_handler.insert(data)

        logger.info('Starting run task')
        try:
            data = self.target(self.args)
        except Exception as e:
            logger.exception('Task Failed')
            update_data = {'status': consts.TASK_FAILED, 'error': str(e)}
            task_handler.update_attr(self.args.task_id, update_data)
        else:
            logger.info('Task Finished')
            logger.debug('Result: %s', data)

            data['result'] = jsonutils.dumps(data.get('result', {}))
            task_handler.update_attr(self.args.task_id, data)
