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

    sql_template = "select * from %s where task_id='%s'"
    query_sql = sql_template % ('tasklist', task_id)
    data = common_utils.translate_to_str(influx_utils.query(query_sql))

    def _zero():
        return common_utils.result_handler(0, [])

    def _one():
        query_sql = sql_template % (measurement, task_id)
        data = common_utils.translate_to_str(influx_utils.query(query_sql))

        return common_utils.result_handler(1, data)

    def _two():
        message = data[0]['error']
        return common_utils.result_handler(2, message)

    try:
        status = data[0]['status']

        switcher = {
            0: _zero,
            1: _one,
            2: _two
        }
        func = switcher.get(status, lambda: 'nothing')
        return func()
    except IndexError:
        message = 'no such task'
        return common_utils.error_handler(message)
