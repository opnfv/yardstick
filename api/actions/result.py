import logging

from api.utils import influx as influx_utils
from api.utils import common as common_utils
from api import conf

logger = logging.getLogger(__name__)


def getResult(args):
    try:
        measurement = args['measurement']
        task_id = args['task_id']
    except KeyError:
        message = 'measurement and task_id must be needed'
        return common_utils.error_handler(message)

    measurement = conf.TEST_CASE_PRE + measurement

    query_sql = "select * from $table where task_id='$task_id'"
    param = {'table': 'tasklist', 'task_id': task_id}
    data = common_utils.translate_to_str(influx_utils.query(query_sql, param))

    def _unfinished():
        return common_utils.result_handler(0, [])

    def _finished():
        param = {'table': measurement, 'task_id': task_id}
        data = common_utils.translate_to_str(influx_utils.query(query_sql,
                                                                param))

        return common_utils.result_handler(1, data)

    def _error():
        return common_utils.result_handler(2, data[0]['error'])

    try:
        status = data[0]['status']

        switcher = {
            0: _unfinished,
            1: _finished,
            2: _error
        }
        return switcher.get(status, lambda: 'nothing')()
    except IndexError:
        return common_utils.error_handler('no such task')
