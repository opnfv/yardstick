from __future__ import absolute_import
from yardstick.benchmark.core import Param
from api import client


def change_osloobj_to_paras(args):
    param = Param({})
    for k in vars(param):
        if hasattr(args, k):
            setattr(param, k, getattr(args, k))
    return param


class Commands(object):
    def __init__(self):
        self.client = client

    def _change_to_dict(self, args):
        p = Param({})
        return {k: getattr(args, k) for k in vars(p) if hasattr(args, k)}
