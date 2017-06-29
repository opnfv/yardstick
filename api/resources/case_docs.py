import os
import logging

from api.utils.common import result_handler
from yardstick.common import constants as consts

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)


def default(args):
    return get_case_docs(args)


def get_case_docs(args):
    try:
        case_name = args['case_name']
    except KeyError:
        return result_handler(consts.API_ERROR, 'case_name must be provided')

    docs_path = os.path.join(consts.DOCS_DIR, '{}.rst'.format(case_name))

    if not os.path.exists(docs_path):
        return result_handler(consts.API_ERROR, 'case not exists')

    LOG.info('Reading %s', case_name)
    with open(docs_path) as f:
        content = f.read()

    return result_handler(consts.API_SUCCESS, {'docs': content})
