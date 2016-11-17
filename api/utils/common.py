import collections

from api.utils.daemonthread import DaemonThread
from yardstick.cmd.cli import YardstickCLI


def translate_to_str(object):
    if isinstance(object, collections.Mapping):
        return {str(k): translate_to_str(v) for k, v in object.items()}
    elif isinstance(object, list):
        return [translate_to_str(ele) for ele in object]
    elif isinstance(object, unicode):
        return str(object)
    return object


def get_command_list(command_list, opts, args):

    command_list.append(args)

    command_list.extend(('--{}'.format(k) for k in opts if 'task-args' != k))
    key = 'task-args'
    key in opts.keys() and command_list.extend(['--task-args', opts[key]])

    return command_list


def exec_command_task(command_list, task_id):   # pragma: no cover
    daemonthread = DaemonThread(YardstickCLI().api, (command_list, task_id))
    daemonthread.start()


class Url(object):

    def __init__(self, url, resource, endpoint):
        super(Url, self).__init__()
        self.url = url
        self.resource = resource
        self.endpoint = endpoint
