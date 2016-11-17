from api.utils.daemonthread import DaemonThread
from yardstick.cmd.cli import YardstickCLI


def translate_to_str(object):
    if isinstance(object, dict):
        dic = {str(k): translate_to_str(v) for k, v in object.items()}
        return dic
    elif isinstance(object, list):
        return [translate_to_str(ele) for ele in object]
    elif isinstance(object, unicode):
        return str(object)
    return object


def get_command_list(command_list, opts, args):

    command_list.append(args)

    for key in opts.keys():
        if 'task-args' != key:
            command_list.append('--' + key)
    if 'task-args' in opts.keys():
        command_list.append('--' + 'task-args')
        command_list.append(str(opts['task-args']))

    return command_list


def exec_command_task(command_list, task_id):   # pragma: no cover
    daemonthread = DaemonThread(YardstickCLI().api, (command_list, task_id))
    daemonthread.start()


class Url(object):

    def __init__(self, url, resource, endpoint):
        self.url = url
        self.resource = resource
        self.endpoint = endpoint
