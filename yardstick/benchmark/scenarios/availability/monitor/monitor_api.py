##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd. and others
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################
import logging
import multiprocessing
import subprocess
import traceback
import time

import yardstick.common.utils as utils
import basemonitor as basemonitor

LOG = logging.getLogger(__name__)


def _execute_shell_command(command):
    '''execute shell script with error handling'''
    exitcode = 0
    output = []
    try:
        output = subprocess.check_output(command, shell=True)
    except Exception:
        exitcode = -1
        output = traceback.format_exc()
        LOG.error("exec command '%s' error:\n " % command)
        LOG.error(traceback.format_exc())

    return exitcode, output


# def _monitor_process(cls, config, queue, event):
# 
#     total_time = 0
#     outage_time = 0
#     total_count = 0
#     outage_count = 0
#     first_outage = 0
#     last_outage = 0
# 
#     wait_time = config.get("duration", 0)
#     monitor_instance = cls(config)
# 
#     queue.put("started")
# 
#     begin_time = time.time()
#     while True:
# 
#         total_count = total_count + 1
# 
#         one_check_begin_time = time.time()
# 
#         ret = monitor_instance.one_request()
# 
#         one_check_end_time = time.time()
# 
#         if ret:
#             outage_count = outage_count + 1
# 
#             outage_time = outage_time + (
#                 one_check_end_time - one_check_begin_time)
# 
#             if not first_outage:
#                 first_outage = one_check_begin_time
# 
#             last_outage = one_check_end_time
# 
#         if event.is_set():
#             print "the monitor process stop"
#             break
# 
#         if wait_time > 0:
#             time.sleep(wait_time)
# 
#     end_time = time.time()
#     total_time = end_time - begin_time
# 
#     queue.put({"total_time": total_time,
#                "outage_time": last_outage-first_outage,
#                "total_count": total_count,
#                "outage_count": outage_count})
# 
# 
# class MonitorProxy(object):
# 
#     def __init__(self):
#         self._result = []
#         self._monitor_process = []
# 
#     def setup(self, config):
#         self._config = config
#         monitor_type = config["monitor_type"]
#         self._monitor_cls = BaseMonitor.get_monitor_cls(monitor_type)
# 
#     def start(self):
# 
# 
#         self._queue = multiprocessing.Queue()
#         self._event = multiprocessing.Event()
#         self._monitor_process = multiprocessing.Process(
#             target=_monitor_process, name="Monitor",
#             args=(self._monitor_cls, self._config, self._queue, self._event))
# 
#         self._monitor_process.start()
#         ret = self._queue.get()
#         LOG.debug("the monitor start ret:%s" % ret)
# 
#     def stop(self):
#         self._event.set()
#         self._result = self._queue.get()
#         LOG.debug("stop the monitor process. the result:%s" % self._result)
# 
#     def get_result(self):
#         return self._result
# 
# class BaseMonitor(object):
#     """docstring for BaseMonitor"""
# 
#     @staticmethod
#     def get_monitor_cls(monitor_type):
#         '''return monitor class of specified type'''
# 
#         for monitor in utils.itersubclasses(BaseMonitor):
#             if monitor_type == monitor.__monitor_type__:
#                 return monitor
#         raise RuntimeError("No such runner_type %s" % monitor_type)
# 
#     def setup(self, config):
#         pass
# 
#     def one_request(self):
#         pass
# 
class MonitorApi(basemonitor.BaseMonitor):
    """docstring for MonitorApi"""

    __monitor_type__ = "openstack-api"

    def one_request(self):
        cmd = self._config["monitor_api"]
        exit_status, stdout = _execute_shell_command(cmd)
        return exit_status


# class MonitorMgr(object):
#     """docstring for MonitorMgr"""
#     def __init__(self):
#         super(MonitorMgr, self).__init__()
# 	self._monitor_list = []
# 
#     def setup(self, config):
#         LOG.debug("monitorMgr config: %s" % config)
#         monitor_cfg = config
# 
#         for cfg in monitor_cfg:
#             instance_count = cfg.get("instance_count", 1)
#             for count in range(instance_count):
#                 monitor_instance = MonitorProxy()
#                 monitor_instance.setup(cfg)
# 
#                 self._monitor_list.append(monitor_instance)
# 
# 
#     def do_monitor(self):
#         for _monotor_instace in self._monitor_list:
#             _monotor_instace.start()
# 
#     def stop_monitor(self):
#         for _monotor_instace in self._monitor_list:
#             _monotor_instace.stop()
# 
#     def get_result(self):
# 
#         total_time = 0
#         outage_time = 0
#         total_count = 0
# 	outage_count = 0
# 
# 	for _monotor_instace in self._monitor_list:
# 	    _result = _monotor_instace.get_result()
# 	    total_time += _result["total_time"]
# 	    outage_time += _result["outage_time"]
# 	    total_count += _result["total_count"]
# 	    outage_count += _result["outage_count"]
# 
# 	ret = {
#             "total_time": total_time,
#             "outage_time": outage_time,
#             "total_count": total_count,
#             "outage_count": outage_count
#         }
# 
#         return ret

if __name__ == '__main__':

    config = {
        'monitor_api': 'nova image-list',
        'monitor_type': 'openstack-api',
        'instance_count':5 
    }

    monitor_configs = []
    monitor_configs.append(config)


    #monitor_type = config["monitor_type"]
    #monitor_cls = basemonitor.BaseMonitor.get_monitor_cls(monitor_type)
    #p = monitor_cls(config)
    #p.setup(config)
    #p = basemonitor.MonitorGroup()
    #p.setup(config)
    #p.start()
    #time.sleep(5)
    #p.stop_monitor()
    #print p.get_result()

    p = basemonitor.MonitorMgr()
    p.setup(monitor_configs)
    p.do_monitor()
    time.sleep(5)
    p.stop_monitor()
    ret = p.get_result()
    print "the result:", ret
    
