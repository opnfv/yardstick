import threading
import os
import datetime

from api import conf
from api.utils.influx import write_data_tasklist


class DaemonThread(threading.Thread):

    def __init__(self, method, args):
        threading.Thread.__init__(self, target=method, args=args)
        self.method = method
        self.command_list = args[0]
        self.task_id = args[1]

    def run(self):
        timestamp = datetime.datetime.now()

        try:
            write_data_tasklist(self.task_id, timestamp, 0)
            self.method(self.command_list, self.task_id)
            write_data_tasklist(self.task_id, timestamp, 1)
        except Exception, e:
            write_data_tasklist(self.task_id, timestamp, 2, error=str(e))
        finally:
            if os.path.exists(conf.TEST_SUITE_PATH + self.task_id + '.yaml'):
                os.remove(conf.TEST_SUITE_PATH + self.task_id + '.yaml')
