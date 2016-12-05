from __future__ import absolute_import
from yardstick.benchmark.core import Param


def change_osloobj_to_paras(args):
    param = Param({})
    for k in param.__dict__:
        if hasattr(args, k):
            setattr(param, k, getattr(args, k))
    return param
