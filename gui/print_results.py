import zmq
import sys
import os
import time
import json
import paramiko
import base64
import logging
import math
import numpy
import commands
import yaml

# --- Static declation of variables ------
LLC_CACHE_MISS = "LONGEST_LAT_CACHE.MISS"
CPU_CLK_THREAD = "CPU_CLK_UNHALTED.THREAD"
CPU_REF_XCLK = "CPU_CLK_UNHALTED.REF_XCLK"
INST_RETIRED = "INST_RETIRED.ANY"
IPC = "IPC"
Hz = "Hz"
DOMAIN = "CORE"
ID = "ID"

# -- Static declration of Variables for testcase --
TX_THROUGHPUT_FPS = "tx_throughput_fps"
RX_THROUGHPUT_FPS = "rx_throughput_fps"
TX_THROUGHPUT_MBPS = "tx_throughput_mbps"
RX_THROUGHPUT_MBPS = "rx_throughput_mbps"
TX_THROUGHPUT_PC_LINERATE = "tx_throughput_pc_linerate"
RX_THROUGHPUT_PC_LINERATE = "rx_throughput_pc_linerate"
MAX_LATENCY = "max_latency"
MIN_LATENCY = "min_latency"
AVG_LATENCY = "avg_latency"

resource = ["CSC", "TSC", "CPU_CLK_UNHALTED.REF_XCLK",
            "CPU_CLK_UNHALTED.THREAD", "OCC"]
result = ["ID", "Hz(GHz)", "IPC", "INSTRUCTION", "BRANCH_MISSES", "L1I_Miss",
          "L2RD_Miss", "LLC_LOAD_Miss", "DTLB_LMiss", "DTLB_SMiss", "ITLB_LMiss"]


class PrintResults():

    """
    This pretty prints the results of testcase for SAE VNF
    """

    def __init__(self):
        self.tc_path = "/tmp/yardstick.out"

    def _dump_stats(self, core):
        kpis = core["Values"]
        print "\n{:>50}".format("CPU core KPIs")
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        print "{:>0} {:>5} {:>5} {:>15} {:>15} {:>15} {:>15} {:>15} {:>15} {:>15}".format(*result)
        print "------------------------------------------------------------------------------------------------------------------------------------------------"

        for kpi in kpis:
            cores = []
            events = kpi['AggEvents']
            cores.append(str(kpi['Id']))
            cores.append(str(round(float(events['Hz']) / 100000000000.0, 2)))
            cores.append(str(round(float(events['IPC']), 2)))
            cores.append(str(events['INSTRUCTION']))
            cores.append(str(events['BRANCH_MISSES']))
            cores.append(str(events['L1_ICACHE_LOAD_MISS']))
            cores.append(str(events['L2_RQSTS.CODE_RD_MISS']))
            cores.append(str(events['LLC_LOAD_MISSES']))
            cores.append(str(events["DTLB_LOAD_MISSES"]))
            cores.append(str(events["DTLB_STORE_MISSES"]))
            cores.append(str(events["ITLB_LOAD_MISSES"]))

            print "{:>0} {:>3} {:>8} {:>15} {:>15} {:>15} {:>15} {:>15} {:>15} {:>15}".format(*cores)
        print "------------------------------------------------------------------------------------------------------------------------------------------------"

    def pmd_stats_display(self, v):
        for k1, v1 in v.items():
            if isinstance(v1, dict):
                if len(v1) == 0:
                    continue
                print k1
                for k2, v2 in v1.items():
                    print('{:>30}  : {:<70}'.format(k2, v2))
            else:
                print('{:>30}  : {:<70}'.format(k1, v1))

    def memory_bw(self, v):
        v = yaml.load(v)
        key = []
        value = []
        for k1, v1 in v["Values"][0]["system memory"][0].items():
            key.append(k1)
            value.append(v1)

        print "\n{:>50}".format("Memory KPIs")
        print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        print('{:>0} (MB/s) {:>30} (MB/s) {:>30} (MB/s)'.format(*key))
        print "-----------------------------------------------------------------------------------------------------------"
        print('{:>10} {:>40} {:>40}'.format(*value))
        print "-----------------------------------------------------------------------------------------------------------\n\n"

    def display_resource_kpis(self, stats):
        for key, value in stats.items():
            if key == "ovs_stats":
                if len(value) == 0 or len(value["dp_stats"]) == 0 or len(value["pmd_stats"]) == 0:
                    continue

                if isinstance(value, dict):
                    if len(value) == 0:
                        continue
                    print key + ":"
                    for k, v in value.items():
                        if isinstance(v, dict):
                            if len(v) == 0:
                                continue
                            print k + ":"
                            self.pmd_stats_display(v)
                        else:
                            if k == "memory":
                                print "Memory :"
                            else:
                                print('{:>30}  : {:<70}'.format(k, v))
            elif key == "memory":
                if len(value) != 0:
                    self.memory_bw(value)
            else:
                if len(value) != 0:
                    core = yaml.load(value)
                    self._dump_stats(core)

    def __print_yardstick_results(self, test_case):
        os.system("clear")
        txt = open(self.tc_path)
        print
        print "---------------------------------------------------------------------------------------------------"
        print "******************  Test Case ({0})  Results ************************".format(test_case)
        print "---------------------------------------------------------------------------------------------------"
        print
        lines = txt.readlines()
        lines.pop(0)
        line = lines.pop(len(lines) - 1)
        latency = {}
        tc_res = json.loads(line)
        tg = tc_res["benchmark"]["data"]["tg__1"]
        if tg != None and len(tg) > 1:
            print "----------------------------------------------------------------------------------------------------"
            print "                                     traffic generator stats					   "
            print "----------------------------------------------------------------------------------------------------"
            for key, value in tg.items():
                if key == "xe0":
                    print "\nnic xe0 details:"
                    print "----------------------"
                    for nkey, nvalue in tg["xe0"].items():
                        if nkey == "latency":
                            latency.update({"xe0": nvalue})
                        else:
                            print('{:>30}  : {:<70}'.format(nkey, nvalue))
                elif key == "xe1":
                    print "\nnic xe1 details:"
                    print "----------------------"
                    for nkey, nvalue in tg["xe1"].items():
                        if nkey == "latency":
                            latency.update({"xe1": nvalue})
                        else:
                            print('{:>30}  : {:<70}'.format(nkey, nvalue))
                else:
                    print('{:>30}  : {:<70}'.format(key, value))

        if len(latency) != 0:
            curr_latency = {}
            for key, value in latency.items():
                if isinstance(value, dict) and "Store-Forward_Avg_latency_ns" in value.keys():
                    curr_latency = value
                else:
                    curr_latency = value['1']['latency']
                print "+++++++++++++++++++++++++++++++"
                print "\nLatency Details ({0}):".format(key)
                print "----------------------"
                for k, v in curr_latency.items():
                    if k != "histogram":
                        print('{:>30}  : {:<70}'.format(k, v))

        print
        print "----------------------------------------------------------------------------------------------------"
        print "                                     VNF KPIs						           "
        print "----------------------------------------------------------------------------------------------------"
        vnf = tc_res["benchmark"]["data"]["vnf__1"]
        for key, value in vnf.items():
            if key != "collect_stats" and key != "collect_kpis":
                if isinstance(value, dict):
                    print key
                    for k, v in value.items():
                        print('{:>30}  : {:<70}'.format(k, v))
                else:
                    print key, ' \t\t\t: ', value

        tc_res = json.loads(line)
        tg_data = tc_res["benchmark"]["data"]
        if "tg__2" in tg_data.keys():
            tg = tg_data["tg__2"]
            if tg != None and len(tg) > 1:
                print
                print "----------------------------------------------------------------------------------------------------"
                if "Total packets verified" in tg.keys():
                    print "                                     Verfier KPIs  						   "
                else:
                    print "                                     L4replay KPIs  						   "
                print "----------------------------------------------------------------------------------------------------"
                for key, value in tg.items():
                    print('{:>30}  : {:<70}'.format(key, value))

        print
        print "----------------------------------------------------------------------------------------------------"
        print "                                     NFVi KPIs						   "
        print "----------------------------------------------------------------------------------------------------"

        stats = vnf["collect_stats"]
        self.display_resource_kpis(stats)

    def print_yardstick_results(self, test_case):
        # try:
        self.__print_yardstick_results(test_case)
        # except:
        # print "Failed to parse the result. Please check the logs for more
        # details."

if __name__ == '__main__':
    c = PrintResults()
    c.print_yardstick_results("test_case")
