import threading
import os
import datetime
import errno

from api import conf
from api.utils.influx import write_data_tasklist


class DaemonThread(threading.Thread):

    def __init__(self, method, args):
        super(DaemonThread, self).__init__(target=method, args=args)
        self.method = method
        self.command_list = args[0]
        self.task_id = args[1]

    def run(self):
        timestamp = datetime.datetime.now()

        try:
            write_data_tasklist(self.task_id, timestamp, 0)
            self.method(self.command_list, self.task_id)
            write_data_tasklist(self.task_id, timestamp, 1)
        except Exception as e:
            write_data_tasklist(self.task_id, timestamp, 2, error=str(e))
        finally:
            _handle_testsuite_file(self.task_id)


def _handle_testsuite_file(task_id):
    try:
        os.remove(os.path.join(conf.TEST_SUITE_PATH, task_id + '.yaml'))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
