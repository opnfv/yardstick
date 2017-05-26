import os
import sys
import commands
import re
import yaml
# from yardstick import ssh


class TestReport():

    def __init__(self):
        gui_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(gui_dir)
        pod_yaml = ""

        self.summary = gui_dir + "/static/summary.html.erb"
        self.error = gui_dir + "/static/error.html.erb"
        self.html = gui_dir + "/static/summary.html"

        with open("/etc/yardstick/nodes/pod.yaml") as fh:
            pod_yaml = yaml.load(fh.read())

        self._vnf = pod_yaml["nodes"][1]
        self.connection = ssh.SSH(self._vnf["user"], self._vnf["ip"],
                                  password=self._vnf["password"])

        self.connection.wait()
        self.hostconnection = ssh.SSH(self._vnf["user"], self._vnf["host"],
                                      password=self._vnf["password"])
        self.hostconnection.wait()

    def execute(self, cmd):
        err, out, _ = self.connection.execute(cmd)
        return out

    def hostexecute(self, cmd):
        err, out, _ = self.hostconnection.execute(cmd)
        return out

    def system_details(self):
        sys_details = {}

        # Platform
        out = self.hostexecute(
            "dmidecode | grep -i  'Processor Information' | wc -l")
        sys_details.update({"platfrorm": out})

        # Platform
        out = self.hostexecute("grep -i HT /proc/cpuinfo")
        if out != "":
            sys_details.update({"HT": "Hyperthreading Enabled"})
        else:
            sys_details.update({"HT": "Hyperthreading Disabled"})

        # CPU version
        cpu = self.hostexecute("lscpu | grep -i  'Model name'")
        version = cpu.split(":")[1].strip()
        sys_details.update({"cpu_version": version})

        # CPU cores
        cores = self.hostexecute("nproc")
        sys_details.update({"cpu_cores": cores})

        # Memory size
        memory = self.hostexecute("free -h | gawk  '/Mem:/{print $2}'")
        sys_details.update({"memory": memory})

        # lspci NIC details
        vpci = self._vnf['interfaces']['xe0']['vpci']
        nics = self.hostexecute(
            "lspci -vmmks {0} | grep -i SDevice".format(vpci))

        nic_10g = nics.split(":")
        if len(nics) > 1:
            nic = nic_10g[1].strip()
        else:
            nic = nic_10g[0].strip()

        sys_details.update({"nic": nic})

        # hugepages 2M
        huge_2m = self.execute(
            "cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages")
        sys_details.update({"huge_2m": huge_2m})

        # hugepages 1G
        huge_1g = self.execute(
            "cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages")
        sys_details.update({"huge_1g": huge_1g})

        # os
        os = self.execute("lsb_release -a | grep -i Description")
        os = os.split(":").pop().strip()
        sys_details.update({"os": os})

        # kernel
        kernel = self.execute("uname -r")
        sys_details.update({"kernel": kernel})

        # bios date
        date = self.hostexecute(
            "dmidecode -t bios | gawk  '/Release Date:/{print $3}'")
        sys_details.update({"bios_date": date})

        # bios version
        bios = self.hostexecute(
            "dmidecode -t bios | gawk  '/Version:/{print $2}'")
        sys_details.update({"bios_version": bios})

        # bios version
        kvm = self.hostexecute("kvm -version")
        sys_details.update({"kvm": kvm.split(", ")[0]})

        return sys_details

    def get_result(self, out, tc, pkt, test_type):
        results = {}
        final = out.pop()
        result = yaml.load(final)

        tg__1 = result["benchmark"]["data"]["tg__1"]
        if tg__1 != None and len(tg__1) > 1 and test_type in ('throughput', 'latency', 'throughput_ixia', 'latency_ixia'):
            results.update({"CurrentDropPercentage": tg__1["DropPercentage"]})
            results.update(
                {"Throughput": float(tg__1["Throughput"]) / (1000000.0)})

        results.update({"testcase": os.path.splitext(tc)[0].upper()})
        results.update({"packet_size": pkt})
        results.update({"iteration": result})

        return results

    def create_html(self, result, test):
        template = ""
        # Create html file
        template = open(self.summary, 'r').read()

        template = template.replace(
            "#testCase", str(result['tc_result']['testcase']))
        template = template.replace(
            "#pktsize", str(result['tc_result']['packet_size']))

        template = template.replace(
            "#socket", "Xeon ({0} socket)".format(str(result['sys']['platfrorm'])))
        template = template.replace(
            "#version", str(result['sys']['cpu_version']))
        template = template.replace("#cores", "{0}({1})".format(
            result['sys']['cpu_cores'], result['sys']['HT']))
        template = template.replace("#ram", str(result['sys']['memory']))
        template = template.replace(
            "#ports", str(result['sys']['nic']) + "(Physical)")
        template = template.replace(
            "#biosversion", str(result['sys']['bios_version']))
        template = template.replace(
            "#biosdate", str(result['sys']['bios_date']))
        template = template.replace("#os", str(result['sys']['os']))
        if test["deployment_type"] == "baremetal":
            template = template.replace(
                "#kernel", str(result['sys']['kernel']))
        else:
            template = template.replace("#kernel", "{0} ({1})".format(
                str(result['sys']['kernel']), str(result['sys']['kvm'])))

        template = template.replace(
            "#hugepages_2M", str(result['sys']['huge_2m']))
        template = template.replace(
            "#hugepages_1G", str(result['sys']['huge_1g']))

        template = template.replace("#vnf_title", str(test["vnf"]).upper())
        template = template.replace("#vnf_testcase", str(test["test_type"]))
        template = template.replace(
            "#vnf_description", str(test["vnf_description"]))
        template = template.replace(
            "#vnfplatform", str(test["deployment_type"]).upper())

        if test["deployment_type"] == "baremetal":
            template = template.replace(
                "#guest", str(test["deployment_type"]).upper())
        else:
            template = template.replace("#guest", str("guest VM").upper())

        tg__1 = (result['tc_result']['iteration'][
                 'benchmark']['data']['tg__1'])

        tg__1_xe0 = {}
        if tg__1 != None and len(tg__1) > 1:
            if "xe0" in tg__1.keys():
                tg__1_xe0 = tg__1['xe0']

                template = template.replace(
                    "#xe0_in_packets", str(tg__1_xe0['in_packets']))
                template = template.replace(
                    "#xe0_out_packets", str(tg__1_xe0['out_packets']))
                if "tx_throughput_fps" in tg__1_xe0.keys():
                    template = template.replace(
                        "#xe0_tx_fps", str(tg__1_xe0['tx_throughput_fps']))
                    template = template.replace(
                        "#xe0_rx_fps", str(tg__1_xe0['rx_throughput_fps']))
                else:
                    template = template.replace(
                        "#xe0_tx_fps", str(tg__1_xe0['tx_throughput_kps']))
                    template = template.replace(
                        "#xe0_rx_fps", str(tg__1_xe0['rx_throughput_kps']))
                template = template.replace(
                    "#xe0_tx_mbps", str(tg__1_xe0['tx_throughput_mbps']))
                template = template.replace(
                    "#xe0_rx_mbps", str(tg__1_xe0['rx_throughput_mbps']))
                template = template.replace("#trafficgen", str(''))
                template = template.replace("#httphead", str(''))
                template = template.replace("#httpdata", str(''))
                template = template.replace(
                    "#httpgen", str('style="display:none"'))
            elif test["test_type"] in ("http_tests", "attacker_tests"):
                tg__1_xe0 = tg__1
                template = template.replace(
                    "#trafficgen", str('style="display:none"'))
                httphead = ""
                httpdata = ""
                for key, value in tg__1.iteritems():
                    httphead += '<th class="head">{0}</th>'.format(key)
                    httpdata += '<td>{0}</td>'.format(value)
                template = template.replace("#httphead", str(httphead))
                template = template.replace("#httpdata", str(httpdata))
        else:
            template = template.replace(
                "#httpgen", str('style="display:none"'))
            template = template.replace(
                "#trafficgen", str('style="display:none"'))
            template = template.replace("#httphead", str(''))
            template = template.replace("#httpdata", str(''))

        if 'latency' in tg__1_xe0.keys():
            latency = {}
            template = template.replace("#latencydisplay", str(''))
            template = template.replace("#overallresult", str(''))

            latencyhead = ''
            latencydata = ''

            if isinstance(tg__1_xe0['latency'], dict) and "Store-Forward_Avg_latency_ns" in tg__1_xe0['latency'].keys():
                latency = tg__1_xe0
            else:
                latencyhead += "<th class='head'>dropped</th>"
                latency = tg__1_xe0['latency']['1']
                latencydata += "<td>" + \
                    str(latency['err_cntrs']['dropped']) + "</td>"
            for key, value in latency['latency'].iteritems():
                if not key in ("histogram", "last_max", "total_max"):
                    latencyhead += "<th class='head'>" + key + "</th>"
                    latencydata += "<td>" + str(value) + "</td>"
            template = template.replace("#latencyheader", latencyhead)
            template = template.replace("#latencydata", latencydata)

            res = "The tolerated packet loss for the tests was {0}.".format(
                str(result['tc_result']['CurrentDropPercentage']))
            template = template.replace("#kpihead", str('KPI (latency) (us)'))
            if isinstance(tg__1_xe0['latency'], dict) and "Store-Forward_Avg_latency_ns" in tg__1_xe0['latency'].keys():
                template = template.replace("#latencyresults", str('{0} with Average latency (us) {1}').format(
                    res, int(latency['latency']['Store-Forward_Avg_latency_ns'])))
                template = template.replace("#kpidata", str('{0}').format(
                    int(latency['latency']['Store-Forward_Avg_latency_ns'])))
            else:
                latency = tg__1_xe0['latency']
                template = template.replace("#latencyresults", str('{0} with Average latency (us) {1}').format(
                    res, round(latency['1']['latency']['average'], 2)))
                template = template.replace(
                    "#kpidata", str('{0}').format(round(latency['1']['latency']['average'], 2)))

            descp = "The KPI is the average latency in us {0} packets with an accepted minimal packet loss".format(
                result['tc_result']['packet_size'])
            template = template.replace("#vnfdescription", str(descp))
        else:
            template = template.replace(
                "#latencydisplay", str('style="display:none"'))
            if test["test_type"] == "throughput" or test["test_type"] == "throughput_ixia":
                template = template.replace("#overallresult", str(''))
                template = template.replace(
                    "#kpihead", str('KPI (throughput) (MPPS)'))
                template = template.replace(
                    "#kpidata", str('{0}').format(result['tc_result']['Throughput']))
                res = "Got Throughput {0} MPPS with packet loss of {1} %.".format(
                    str(result['tc_result']['Throughput']), str(result['tc_result']['CurrentDropPercentage']))
                template = template.replace(
                    "#latencyresults", str('{0}').format(res))
                descp = "The KPI is the number of packets per second for {0} packets with an accepted minimal packet loss".format(
                    result['tc_result']['packet_size'])
                template = template.replace("#vnfdescription", str(descp))
                template = template.replace("#latencyheader", str(''))
                template = template.replace("#latencydata", str(''))
            if test["test_type"] == "verification":
                template = template.replace(
                    "#overallresult", str('style="display:none"'))
                template = template.replace("#latencyheader", str(''))
                template = template.replace("#latencydata", str(''))
                tg__3 = (result['tc_result']['iteration'][
                         'benchmark']['data']['tg__2'])
                template = template.replace(
                    "#kpihead", str('KPI (verfication)'))
                if "Total packets mismatch" in tg__3.keys() and str(tg__3["Total packets mismatch"]) == "0":
                    template = template.replace(
                        "#kpidata", str('{0}').format("pass"))
                    template = template.replace("#latencyresults", str(
                        'Verification Test passed without any packet mismatch'))
                else:
                    template = template.replace(
                        "#kpidata", str('{0}').format("fail"))
                    template = template.replace("#latencyresults", str(
                        'Verification Test failed with packet mismatch'))

                descp = "The KPI is packet verification for any mismatch @destination for {0} packets".format(
                    result['tc_result']['packet_size'])
                template = template.replace("#vnfdescription", str(descp))
            if test["test_type"] in ("http_tests", "attacker_tests"):
                template = template.replace(
                    "#overallresult", str('style="display:none"'))
                template = template.replace("#latencyheader", str(''))
                template = template.replace("#latencydata", str(''))
                template = template.replace(
                    "#kpihead", str('requests_per_second [#/sec] (mean)'))
                template = template.replace("#kpidata", str('{0}').format(
                    tg__1_xe0['requests_per_second [#/sec] (mean)']))
                template = template.replace("#latencyresults", str(
                    'Number of request served per second : {0}').format(tg__1_xe0['requests_per_second [#/sec] (mean)']))
                descp = "The KPI is request served per second with an accepted minimal packet loss"
                template = template.replace("#vnfdescription", str(descp))

        if test["test_type"] in ('throughput', 'latency', 'throughput_ixia', 'latency_ixia'):
            template = template.replace(
                "#testCase", str(result['tc_result']['testcase']))
            template = template.replace(
                "#thoughput", str(result['tc_result']['Throughput']))
            template = template.replace(
                "#drop", str(result['tc_result']['CurrentDropPercentage']))
            template = template.replace(
                "#pktsize", str(result['tc_result']['packet_size']))
            if "txtputgraph" in result:
                template = template.replace(
                    "<!--#txtputgraph-->", result["txtputgraph"])
        vnf__2 = (result['tc_result']['iteration'][
                  'benchmark']['data']['vnf__1'])
        vnf_kps_headers = ""
        vnf_kps = ""
        for key, value in vnf__2.iteritems():
            if key != "collect_stats" and key != "collect_kpis":
                vnf_kps_headers += "<th class='head'>" + str(key) + "</th>"
                vnf_kps += "<td>" + str(value) + "</td>"

        template = template.replace("#vnf_kps_headers", str(vnf_kps_headers))
        template = template.replace("#vnf_kps", str(vnf_kps))

        tg_data = (result['tc_result']['iteration']['benchmark']['data'])
        if "tg__2" in tg_data.keys():
            tg__3 = tg_data["tg__2"]
            if tg__3 != None and len(tg__3) > 1:
                if "packets_in" in tg__3.keys():
                    template = template.replace("#l4replaystats", str(''))
                    template = template.replace(
                        "#verifier", str('style="display:none"'))
                    template = template.replace("#nol4verfiy", str(''))
                    template = template.replace(
                        "#l4replay_packets_in", str(tg__3['packets_in']))
                    template = template.replace(
                        "#l4replay_packets_dropped_input", str(tg__3['packets_in_dropped']))
                    template = template.replace(
                        "#l4replay_packets_out", str(tg__3['packets_out']))
                    template = template.replace(
                        "#l4replay_packets_dropped_output", str(tg__3['packets_out_dropped']))
                elif "Total packets mismatch" in tg__3.keys():
                    template = template.replace("#verifier", str(''))
                    template = template.replace("#nol4verfiy", str(''))
                    template = template.replace(
                        "#l4replaystats", str('style="display:none"'))
                    template = template.replace(
                        "#verified", str(tg__3['Total packets verified']))
                    template = template.replace(
                        "#match", str(tg__3['Total packets match']))
                    template = template.replace(
                        "#miss", str(tg__3['Total packets mismatch']))
                else:
                    template = template.replace(
                        "#verifier", str('style="display:none"'))
                    template = template.replace(
                        "#l4replaystats", str('style="display:none"'))
                    template = template.replace(
                        "#nol4verfiy", str('style="display:none"'))
            else:
                template = template.replace(
                    "#verifier", str('style="display:none"'))
                template = template.replace(
                    "#l4replaystats", str('style="display:none"'))
                template = template.replace(
                    "#nol4verfiy", str('style="display:none"'))
        else:
            template = template.replace(
                "#verifier", str('style="display:none"'))
            template = template.replace(
                "#l4replaystats", str('style="display:none"'))
            template = template.replace(
                "#nol4verfiy", str('style="display:none"'))

        # NFVi KPIs
        cores = vnf__2['collect_stats']['core']
        if len(cores) == 0:
            #-- hide the table
            template = template.replace("#coredisplay", str('none'))
        else:
            template = template.replace("#coredisplay", str('block'))
            kpis = yaml.load(cores)["Values"]
            values = ""
            for kpi in kpis:
                cores = []
                events = kpi['AggEvents']
                values += "<tr>"
                values += "<td>{0}</td>".format(str(kpi['Id']))
                values += "<td>{0}</td>".format(
                    str(round(float(events['Hz']) / 100000000000.0, 2)))
                values += "<td>{0}</td>".format(
                    str(round(float(events['IPC']), 2)))
                values += "<td>{0}</td>".format(str(events['INSTRUCTION']))
                values += "<td>{0}</td>".format(str(events['BRANCH_MISSES']))
                values += "<td>{0}</td>".format(
                    str(events['L1_ICACHE_LOAD_MISS']))
                values += "<td>{0}</td>".format(
                    str(events['L2_RQSTS.CODE_RD_MISS']))
                values += "<td>{0}</td>".format(str(events['LLC_LOAD_MISSES']))
                values += "<td>{0}</td>".format(
                    str(events['DTLB_LOAD_MISSES']))
                values += "<td>{0}</td>".format(
                    str(events['DTLB_STORE_MISSES']))
                values += "<td>{0}</td>".format(
                    str(events['ITLB_LOAD_MISSES']))
                values += "</tr>"

            template = template.replace("#cpucoredata", str(values))

        ovs_stats = vnf__2['collect_stats']['ovs_stats']

        if len(ovs_stats) == 0 or len(ovs_stats['dp_stats']) == 0 or len(ovs_stats['pmd_stats']) == 0:
            #-- hide the table
            template = template.replace("#ovsdisplay", str('none'))
            template = template.replace("#pmd_data", str(""))
        else:
            template = template.replace("#ovsdisplay", str('block'))
            dp_stats = ovs_stats['dp_stats']
            template = template.replace("#dp_hit", str(dp_stats['hit']))
            template = template.replace("#dp_miss", str(dp_stats['missed']))
            template = template.replace("#dp_lost", str(dp_stats['lost']))

            pmd_stats = ovs_stats['pmd_stats']
            pmd_tr = ""
            for key, value in pmd_stats.iteritems():
                pmd_tr += "<tr>"
                pmd_tr += "<td>{0}</td>".format(value['numa_id'])
                pmd_tr += "<td>{0}</td>".format(value['core_id'])
                pmd_tr += "<td>{0}</td>".format(value['emc hits'])
                pmd_tr += "<td>{0}</td>".format(value['megaflow hits'])
                pmd_tr += "<td>{0}</td>".format(value['miss'])
                pmd_tr += "<td>{0}</td>".format(value['lost'])
                pmd_tr += "<td>{0}</td>".format(value['polling cycles'])
                pmd_tr += "<td>{0}</td>".format(value['processing cycles'])
                if "avg cycles per packet" in value.keys():
                    pmd_tr += "<td>{0}</td>".format(
                        value['avg cycles per packet'])
                else:
                    pmd_tr += "<td>{0}</td>".format(0)
            template = template.replace("#pmd_data", str(pmd_tr))

        sysmemory = vnf__2['collect_stats']['memory']
        if len(sysmemory) != 0:
            sysmemory = yaml.load(sysmemory)
            memory = sysmemory['Values'][0]
            if len(memory) == 0:
                #-- hide the table
                template = template.replace("#memorydisplay", str('none'))
            else:
                template = template.replace("#memorydisplay", str('block'))
                template = template.replace("#memory_write", str(
                    memory['system memory'][0]['System Write Throughput']))
                template = template.replace("#memory_read", str(
                    memory['system memory'][0]['System Read Throughput']))
                template = template.replace("#memory_total", str(
                    memory['system memory'][0]['System Memory Throughput']))
        else:
            template = template.replace("#memorydisplay", str('none'))

        summary = open(self.html, 'w')
        summary.write(template)

    def create_error_html(self, tc, status):
        template = ""
        # Create html file
        template = open(self.error, 'r').read()

        template = template.replace("#testcase", str(tc))
        template = template.replace("#log_file", str(status["logfile"]))
        summary = open(self.html, 'w')
        summary.write(template)

    def final_result(self, test, pkt, status):
        final_result = {}

        tc = test["tc"]
        if status["status"] == 0:
            self.create_error_html(tc, status)
            return

        #----- creating result html -----------
        tmp = ""
        if os.path.isfile("/tmp/yardstick.out"):
            out = open("/tmp/yardstick.out")
            tmp = out.readlines()

        if tmp:
            print "Test successfully completed. Test results stored in /tmp/yardstick.out"
            env = tmp.pop(0)

            hw_details = self.system_details()
            final_result.update({"sys": hw_details})
            tc_result = self.get_result(tmp, tc, pkt, test["test_type"])
            final_result.update({"tc_result": tc_result})
            if "txtputgraph" in status:
                final_result.update({"txtputgraph": status["txtputgraph"]})

            self.create_html(final_result, test)
        else:
            print "Test Failed."
            print "For more information. Please check debug log in {0}".format(log_file)

# c = TestReport()
# c.final_result({'vnf': u'cgnat', 'vnf_description': '', 'tc':
# 'tc_ipv4_16Kflow_64B_packetsize.yaml', 'KPI': ''}, "64B", {"status" : 1,
# "logfile": "logfile"})
