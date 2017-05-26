import os
import string
import subprocess
import yaml
import time
import shutil
import json
from datetime import datetime
from oslo_serialization import jsonutils

from django.shortcuts import render, redirect
from ws4redis.redis_store import RedisMessage
from ws4redis.publisher import RedisPublisher
from celery.decorators import task
from yardstick import ssh

from .forms import RegressionPriorityForm, VNFConfigForm


test_case_list = []
selected_tg = []
gui_path = os.getcwd()
gui_dir = os.path.dirname(gui_path)
test_cases_dir = os.path.join(gui_dir, 'samples/vnf_samples/nsut')
scaleup = False

performance_test_types = (
    'throughput', 'latency', 'throughput_ixia', 'latency_ixia', 'throughput_ixia_multiport', 'latency_ixia_multiport'
    'throughput_multiport', 'latency_multiport')
non_performance_test_types = (
    'functional', 'verification', 'http_tests', 'attacker_tests')


def index(request):
    request.session.flush()
    os.chdir(gui_path)
    tg_types = ['software', 'ixia']
    context = {
        'tg_list': tg_types
    }
    return render(request, 'execute_test/tg_list.html', context)


def initiate_logging(request):
    return render(request, 'execute_test/logging.html', context={})


def get_vnf_list(request, tg_type):
    vnf_types = ['acl', 'cgnat', 'firewall', 'vpe']
    request.session['vnf_types'] = vnf_types[:]
    request.session['tg_type'] = tg_type
    context = {
        'data': vnf_types,
        'next': 'deployment-types',
    }
    selected_tg.append(tg_type)

    return render(request, 'execute_test/list.html', context)


def get_deployment_list(request, vnf_type):
    request.session['vnf_type'] = vnf_type
    if vnf_type == 'regression':
        return redirect('/execute_test/regression')
    return redirect('/execute_test/test-cases')
    cwd = os.getcwd()
    os.chdir('{0}/{1}'.format(test_cases_dir, vnf_type))
    deployment_types = os.listdir('.')
    deployment_types = map(
        string.capitalize, filter(os.path.isdir, deployment_types))
    context = {
        'data': deployment_types,
        'next': 'test-types',
    }
    os.chdir(cwd)
    return render(request, 'execute_test/list.html', context)


def get_test_list(request, deployment_type):
    request.session['deployment_type'] = deployment_type
    vnf_type = request.session['vnf_type']
    exec_dir = os.path.join(
        test_cases_dir, '{0}/{1}'.format(vnf_type, deployment_type))
    cwd = os.getcwd()
    os.chdir(exec_dir)
    test_types = os.listdir('.')
    test_types = filter(os.path.isdir, test_types)

    for test in test_types:
        if request.session['tg_type'] == "IXIA":
            test_types[:] = [value for value in test_types if "ixia" in value]
        else:
            test_types[:] = [
                value for value in test_types if "ixia" not in value]
    if 'scaleup' not in test_types:
        test_types.append('scaleup')
    context = {
        'data':  test_types,
        'next': 'ip-versions',

    }
    os.chdir(cwd)
    return render(request, 'execute_test/list.html', context)


def get_ipversion_list(request, test_type):
    ip_types = ['IPV4', 'IPV6']
    context = {
        'data': ip_types,
        'next': 'packet-types',
    }
    global scaleup
    if test_type == 'scaleup':
        scaleup = True
        test_type = 'throughput'
    else:
        scaleup = False
    request.session['test_type'] = test_type
    if test_type in non_performance_test_types:
        return redirect('/execute_test/test-cases')
    return render(request, 'execute_test/list.html', context)


def get_packsize_list(request, ip_type):
    pack_types = ['64B', '1518B', 'IMIX']
    context = {
        'data': pack_types,
        'next': 'vnf-config'
    }
    request.session['ip_type'] = ip_type
    return render(request, 'execute_test/list.html', context)


def vnf_config(request, packet_type):
    request.session['packet_type'] = packet_type
    if request.session[
            'test_type'] in performance_test_types and request.session[
            'vnf_type'] != 'vpe':
        return redirect('/execute_test/config/vnf')
    return redirect('/execute_test/test-cases')


def get_test_case_list(request):
    packet_type = request.session.get('packet_type', '64b')
#    test_type = request.session['test_type']
    vnf_type = request.session['vnf_type']
#    deployment_type = request.session['deployment_type']
    ip_type = request.session.get('ip_type', 'ipv4')
    cwd = os.getcwd()
    exec_dir = os.path.join(
        test_cases_dir, '{0}/{1}/'.format(
            test_cases_dir, vnf_type))
    os.chdir(exec_dir)
    test_cases = os.listdir('.')
    test_cases = filter(os.path.isfile, test_cases)
    for test_case in test_cases:
        if not test_case.startswith('tc'):
            test_cases.remove(test_case)

    tmp_tests = []
    test_type = 'throughput'
    for vnf in test_cases:
        if "tc_" in vnf.lower():
            tmp_tests.append(vnf)

    if request.session['tg_type'].lower() == "ixia":
         tmp_tests[:] = [value for value in tmp_tests if "ixia" in value or "ixload" in value]
    else:
         tmp_tests[:] = [
              value for value in tmp_tests if "ixia" not in value]
         tmp_tests[:] = [
              value for value in tmp_tests if "ixload" not in value]

    tc_list = []
    global test_case_list
    test_case_list = tmp_tests
    for tc in tmp_tests:
        test = tc.split('.')[0].split('_')[1:]
        tc_list.append(" ".join(test).title())
    os.chdir(cwd)
    context = {
        'test_cases': tc_list
    }
    return render(request, 'execute_test/test_case_list.html', context)


def select_test_case(request, test_id):
    test_case = test_case_list[int(test_id)]
    request.session['test_case'] = test_case
    return redirect('/execute_test/test_case_execution')


def execute_test_case(request):
    print "executing test"
    time.sleep(10)
    if scaleup:
        execute_scaleup.delay(dict(request.session.items()))
    else:
        execute_single_test.delay(dict(request.session.items()))
    return redirect('/execute_test/results')


@task
def execute_single_test(request):
    cwd = os.getcwd()
    vnf_type = request['vnf_type']
    deployment_type = request.get('deployment_type', '')
    test_type = request.get('test_type', '')
    test_case = request.get('test_case', '')

    print test_case
    print test_case
    print test_case
    print test_case
    print test_case
    exec_dir = os.path.join(
        test_cases_dir, '{0}/{1}/'.format(
            test_cases_dir, vnf_type))
    os.chdir(exec_dir)
    # Capture logs :)
    os.system("mkdir -p {0}/logs".format(gui_dir))
    log_file = datetime.now().strftime(
        "{0}/logs/{1}_{2}_{3}_%d_%m_%Y_%H_%M_%S.log".format(
            gui_dir, vnf_type, deployment_type, test_case))
    log_open = open(log_file, 'a')
    #if request['test_type'] in performance_test_types:
    #    vnf_config = {}
    #    vnf_config['worker_config'] = str(request['worker_config'])
    #    vnf_config['lb_count'] = request['lb_count']
    #    vnf_config['lb_config'] = str(request.get('lb_config', 'SW'))
    #    vnf_config['worker_threads'] = request['worker_threads']
    #    with open(test_case) as fh:
    #        tc_yaml = yaml.load(fh.read())
    #    if 'vnf_options' not in tc_yaml['scenarios'][0]:
    #        tc_yaml['scenarios'][0]['vnf_options'] = {}
    #    tc_yaml['scenarios'][0]['vnf_options']['vnf_config'] = vnf_config
    #    yaml.dump(tc_yaml, open(test_case, 'w'))
    redis_publisher = RedisPublisher(facility='logging', broadcast=True)
    command = 'yardstick {1} task start {0}'.format(test_case, '--debug')
    p = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, ''):
        print line
        message = RedisMessage(line)
        redis_publisher.publish_message(message)
        log_open.write(line)
    os.chdir(cwd)


def config_vnf(request):
    form = VNFConfigForm(request.POST or None)
    if form.is_valid():
        request.session['lb_count'] = form.cleaned_data['lb_count']
        request.session['worker_threads'] = form.cleaned_data['worker_threads']
        request.session['worker_config'] = form.cleaned_data[
            'worker_configuration']
        lb_config = form.cleaned_data['lb_config']
        if lb_config == 'HW' and request.session[
                'deployment_type'] == 'baremetal':
            pod_data = yaml.safe_load(
                open('/etc/yardstick/nodes/pod.yaml', 'r').read())
            for interface in pod_data['nodes'][1]['interfaces']:
                if pod_data['nodes'][1]['interfaces'][interface][
                        'driver'].lower() != 'i40e':
                    lb_config = 'SW'
                    break
        else:
            lb_config = 'SW'
        request.session['lb_config'] = lb_config
        return redirect('/execute_test/test-cases')
    context = {
        'form': form,
    }
    return render(
        request, 'execute_test/vnf_config_form.html', context=context)


def show_results(request):
    return render(request, 'execute_test/result_page.html', context={})


def hostexecute(connection, cmd):
    err, out, _ = connection.execute(cmd)
    return out

def get_system_data():
    sys_data = {}
    load = ""
    with open("/etc/yardstick/nodes/pod.yaml", 'r') as stream:
        load = yaml.load(stream)

    vnf  = [node for node in load["nodes"] if node["name"] == "vnf"]
    mgmt_interface = vnf[0]
    connection = ssh.SSH(mgmt_interface["user"], mgmt_interface["ip"],
                         password=mgmt_interface["password"])
    connection.wait()

    cpu = hostexecute(connection, "lscpu | grep -i  'Model name'")
    version = cpu.split(":")[1].strip()
    sys_data.update({"cpu_version": version})

    cores = hostexecute(connection, "nproc")
    sys_data.update({"cpu_cores": cores})
    # Platform
    out = hostexecute(connection, "grep -i HT /proc/cpuinfo")
    if out != "":
        sys_data.update({"HT": "Hyperthreading Enabled"})
    else:
        sys_data.update({"HT": "Hyperthreading Disabled"})

    memory = hostexecute(connection, "free -h | gawk  '/Mem:/{print $2}'")
    sys_data.update({"memory": memory})

    # bios version
    bios = hostexecute(connection,
            "dmidecode -t bios | gawk  '/Version:/{print $2}'")
    sys_data.update({"bios_version": bios})

    date = hostexecute(connection,
            "dmidecode -t bios | gawk  '/Release Date:/{print $3}'")
    sys_data.update({"bios_date": date})

    
    # os
    os = hostexecute(connection, "lsb_release -a | grep -i Description")
    os = os.split(":").pop().strip()
    sys_data.update({"os": os})

    # kernel
    kernel = hostexecute(connection, "uname -r")
    sys_data.update({"kernel": kernel})

    # hugepages 2M
    huge_2m = hostexecute(connection,
            "cat /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages")
    sys_data.update({"huge_2m": huge_2m})

    # hugepages 1G
    huge_1g = hostexecute(connection,
            "cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages")
    sys_data.update({"huge_1g": huge_1g})


    return sys_data


def show_tc_result(request):
    #-------------------Print results-----------------------------------------
    tpl = 'execute_test/result.html'
    if os.path.isfile("/tmp/yardstick.out"):
        lines = []
        with open("/tmp/yardstick.out") as infile:
           lines = jsonutils.load(infile)

        tpl = 'execute_test/result.html'

        data = lines['result']
        tmp_data = data.pop(len(data) - 1)
        if "Total packets verified" in tmp_data['benchmark']['data'].get('tg__2', ''):
            tpl = 'execute_test/result_ver.html'
            data = data.pop(-1)
            tg_2_data = data['benchmark']['data']['tg__2']
            result = 'PASS' if int(tg_2_data['Total packets verified']) == int(
                tg_2_data['Total packets match']) else 'FAIL'
            context = {
                'verified': tg_2_data['Total packets verified'],
                'mismatch': tg_2_data['Total packets mismatch'],
                'match': tg_2_data['Total packets match'],
                'result': result
            }
        elif "failed_requests" in tmp_data['benchmark']['data']['tg__1']:
            tpl = 'execute_test/result_http.html'
            data = tmp_data['benchmark']['data']['tg__1']
            vnf_1_data = [tmp_data['benchmark']['data']['vnf__1']]
            keys = data.keys()
            tmp_data = {}
            for key in keys:
                if key.startswith('requests_served_'):
                    tmp_data[key.split()[0].replace(
                        '_', ' ').title()] = data[key]
            result = 'PASS' if int(data["failed_requests"]) == 0 else 'FAIL'
            context = {
                "result": result,
                "complete_requests": data['complete_requests'],
                'total_time': data['time_taken_for_tests [seconds]'],
                "failed_requests": data["failed_requests"],
                'time_per_request': data.get(
                    'time_per_request [ms] (mean, across all \
concurrent requests)', 0),
                'requests_per_second': data[
                    "requests_per_second [#/sec] (mean)"],
                'vnf_1_data': vnf_1_data,
                'requests_served': tmp_data
            }
        elif 'latency' in tmp_data['benchmark']['data']['tg__1'].get(
                'xe0', {}):
            tpl = 'execute_test/result_lat.html'
            tc = " ".join(data[0][
                          'scenario_cfg']['tc'].split('_')[1:]).title()
            [data.pop(0) for x in range(2)]
            yardstick_data = [line for line in data]
            data = [line for line in data]
            count = sum(
                [1 for line in data if 'latency' not in line['benchmark'][
                    'data']['tg__1']['xe0']])
            throughput_data = [data.pop(0) for x in range(count)]
            for index, line in enumerate(throughput_data):
                timestamp = line['benchmark']['timestamp']
                timestamp = datetime.fromtimestamp(timestamp).strftime(
                    '%d-%m-%Y : %H:%M:%S')
                line['benchmark']['data']['tg__1']['timestamp'] = timestamp
                throughput_data[index] = line
            throughput_data = [line['benchmark']['data']['tg__1'] for line in
                               throughput_data]
            graph_data = [["Iteration", 'TX Throughput MPPS',
                           'RX Throughput MPPS', 'Current Drop Percentage']]
            graph_data_1 = [
                ["Iteration", 'Throughput MPPS', 'Drop Percentage']]
            for index, line in enumerate(throughput_data, 1):
                iterater = 'Iteration {0}'.format(index)
                tmp = []
                tmp_1 = []
                tmp.append(iterater)
                tmp_1.append(iterater)
                tmp.append(round(line['TxThroughput'] / 1000000, 2))
                tmp.append(round(line['RxThroughput'] / 1000000, 2))
                tmp.append(line['CurrentDropPercentage'])
                tmp_1.append(round(line['Throughput'] / 1000000, 2))
                tmp_1.append(line['DropPercentage'])
                graph_data.append(tmp)
                graph_data_1.append(tmp_1)
            tg_1_data = [line['benchmark']['data']['tg__1'] for line in
                         yardstick_data]
            keys = tg_1_data[0].keys()
            if_list = [key for key in keys if key.startswith('xe')]
            graph_data_2_title = ["Iteration"]
            graph_data_2_title.extend(['Average Latency {0}'.format(ifs) for
                                       ifs in if_list])
            graph_data_2 = [graph_data_2_title]
            latency_data = {}
            for index, line in enumerate(data):
                tmp = []
                tmp.append(index + 1)
                for ind, ifs in enumerate(if_list):
                    pg_id = str(ind + 1)
                    timestamp = line['benchmark']['timestamp']
                    timestamp = datetime.fromtimestamp(
                        timestamp).strftime('%d-%m-%Y : %H:%M:%S')
                    line['benchmark']['data']['tg__1']['timestamp'] = timestamp
                    latency = round(
                        line['benchmark']['data']['tg__1'][ifs]['latency'][
                            pg_id]['latency']['average'], 2)
                    line['benchmark']['data']['tg__1']['latency'] = latency
                    jitter = round(line['benchmark']['data']['tg__1'][ifs][
                        'latency'][pg_id]['latency']['jitter'], 2)
                    line['benchmark']['data']['tg__1']['jitter'] = jitter
                    data[index] = line
                    tmp.append(latency)
                    tmp_dir = {
                        'latency': latency,
                        'jitter': jitter,
                        'timestamp': timestamp
                    }
                    tmp_data = latency_data.get(ifs, list())
                    tmp_data.append(tmp_dir)
                    latency_data[ifs] = tmp_data
                graph_data_2.append(tmp)
            data = [line['benchmark']['data']['tg__1'] for line in data]
            lat_data = yardstick_data[-1]
            xe_stats = {}
            for line in tg_1_data:
                for key in if_list:
                    stat = xe_stats.get(key, list())
                    stat.append(line[key])
                    xe_stats[key] = stat
            lat_stats = {}
            for index, interface in enumerate(if_list):
                pg_id = str(index + 1)
                lat_stats[interface] = {
                    'dropped': lat_data['benchmark']['data']['tg__1']['xe0'][
                        'latency'][pg_id]['err_cntrs']['dropped'],
                    'average': lat_data['benchmark']['data']['tg__1']['xe0'][
                        'latency'][pg_id]['latency']['average'],
                    'jitter': lat_data['benchmark']['data']['tg__1']['xe0'][
                        'latency'][pg_id]['latency']['jitter'],
                    'total_min': lat_data['benchmark']['data']['tg__1']['xe0'][
                        'latency'][pg_id]['latency']['total_min'],
                }

            tg_2_data = [line['benchmark']['data']['tg__2'] for line in
                         yardstick_data]
            vnf_1_data = [line['benchmark']['data']['vnf__1'] for line in
                          yardstick_data]
            context = {
                'tc': tc,
                'throughput': "{0} MPPS".format(round(
                    data[-1]['Throughput'] / 1000000, 2)),
                'drop_percentage': data[-1]['DropPercentage'],
                'data': throughput_data,
                'latency_data': latency_data,
                'graph_data': json.dumps(graph_data),
                'graph_data_1': json.dumps(graph_data_1),
                'graph_data_2': json.dumps(graph_data_2),
                'tg_2_data': tg_2_data,
                'vnf_1_data': vnf_1_data,
                'xe_stats': xe_stats,
                'lat_stats': lat_stats
            }

        elif "Throughput" in tmp_data['benchmark']['data']['tg__1']:
            sys_data = get_system_data()
            tc = " ".join(data[0][
                'scenario_cfg']['tc'].split('_')[1:]).title()
            [data.pop(0) for x in range(2)]
            yardstick_data = [line for line in data]
            data = [line for line in data]
            for index, line in enumerate(data):
                timestamp = line['benchmark']['timestamp']
                timestamp = datetime.fromtimestamp(
                    timestamp).strftime('%d-%m-%Y : %H:%M:%S')
                line['benchmark']['data']['tg__1']['timestamp'] = timestamp
                data[index] = line

            data = [line['benchmark']['data']['tg__1'] for line in data]
            graph_data = [
                ["Iteration", 'TX Throughput MPPS', 'RX Throughput MPPS',
                    'Current Drop Percentage']]
            graph_data_1 = [
                ["Iteration", 'Throughput MPPS', 'Drop Percentage']]

            for index, line in enumerate(data, 1):
                iterater = 'Iteration {0}'.format(index)
                tmp = []
                tmp_1 = []
                tmp.append(iterater)
                tmp_1.append(iterater)
                tmp.append(round(line['TxThroughput'] / 1000000, 2))
                tmp.append(round(line['RxThroughput'] / 1000000, 2))
                tmp.append(line['CurrentDropPercentage'])
                tmp_1.append(round(line['Throughput'] / 1000000, 2))
                tmp_1.append(line['DropPercentage'])
                graph_data.append(tmp)
                graph_data_1.append(tmp_1)

            tg_1_data = [line['benchmark']['data']['tg__1'] for line in
                         yardstick_data]
            keys = tg_1_data[0].keys()
            if_list = [key for key in keys if key.startswith('xe')]
            xe_stats = {}
            for line in tg_1_data:
                for key in if_list:
                    stat = xe_stats.get(key, list())
                    stat.append(line[key])
                    xe_stats[key] = stat
            tg_2_data = [line['benchmark']['data'].get('tg__2', '') for line in
                         yardstick_data]
            vnf_1_data = [line['benchmark']['data']['vnf__1'] for line in
                          yardstick_data]
            context = {
                'tc': tc,
                'throughput': "{0} MPPS".format(round(
                    data[-1]['Throughput'] / 1000000, 2)),
                'drop_percentage': data[-1]['DropPercentage'],
                'data': data,
                'graph_data': json.dumps(graph_data),
                'graph_data_1': json.dumps(graph_data_1),
                'tg_2_data': tg_2_data,
                'vnf_1_data': vnf_1_data,
                'sys_data': sys_data,
                'xe_stats': xe_stats
            }
        else:
            tpl = 'execute_test/result_func.html'
            tc = " ".join(data[0][
                          'scenario_cfg']['tc'].split('_')[1:]).title()
            data = data.pop(-1)
            tg_1_data = data['benchmark']['data']['tg__1']
            tg_2_data = data['benchmark']['data']['tg__2']
            vnf_data = data['benchmark']['data']['vnf__1']
            context = {
                'tc': tc,
                'tg1_xe0': tg_1_data['xe0']['out_packets'],
                'tg1_xe1': tg_1_data['xe1']['in_packets'],
                'vnf_rcvd': vnf_data.get('packets_in', 0),
                'vnf_fwd': vnf_data.get('packets_fwd', 0),
                'vnf_drop': vnf_data.get('packets_dropped', 0),
                'tg2_xe0': tg_2_data['xe0']['in_packets'],
                'tg2_xe1': tg_2_data['xe1']['out_packets'],
                'result': vnf_data['tg_test_result :']
            }
    else:
        data = {}
        graph_data = [
            ["Iteration", 'TX Throughput MPPS',
                'RX Throughput MPPS', 'Drop Percentage']]

        context = {
            'data': data,
            'graph_data': json.dumps(graph_data)
        }
    return render(request, tpl, context=context)


def execute_regression(request):
    vnf_types = request.session['vnf_types']
    vnf_types.append('all')
    context = {
        'title': 'VNF Types for Regression',
        'data': vnf_types,
        'next': 'deployment-type'
    }
    return render(request, 'execute_test/list_reg.html', context=context)


def regression_deployment_type(request, vnf_type):
    request.session['vnf_type'] = vnf_type
    if vnf_type == 'all':
        deployment_types = ['baremetal', 'ovs', 'sriov']
    else:
        path = os.path.join(gui_dir, 'isb_samples/nsut/{0}'.format(vnf_type))
        deployment_types = os.listdir(path)
        deployment_types = filter(
            os.path.isdir, [
                os.path.join(path, deployment_type) for deployment_type in
                deployment_types])
        deployment_types = [os.path.split(deployment_type)[1]
                            for deployment_type in deployment_types]

    context = {
        'title': 'Deployment Types',
        'data': deployment_types,
        'next': 'regression-type'
    }
    return render(request, 'execute_test/list_reg.html', context=context)


def regression_type(request, deployment_type):
    request.session['deployment_type'] = deployment_type
    if request.session['vnf_type'] == 'all':
        regression_types = list(
            set(performance_test_types) | set(non_performance_test_types))
    else:
        path = os.path.join(gui_dir, 'isb_samples/nsut/{0}/{1}'.format(
            request.session['vnf_type'], deployment_type))
        regression_types = os.listdir(path)
        regression_types = filter(
            os.path.isdir, [os.path.join(path, regression_type) for
                            regression_type in regression_types])
        regression_types = [os.path.split(regression_type)[1]
                            for regression_type in regression_types]
        if 'scaleup' in regression_types:
            regression_types.remove('scaleup')

    context = {
        'title': 'Regression Type',
        'data': regression_types,
        'next': 'ip-version'
    }
    return render(request, 'execute_test/list_reg.html', context=context)


def regression_ip_version(request, regression_type):
    request.session['regression_type'] = regression_type
    if regression_type in non_performance_test_types:
        return redirect('/execute_test/regression/regression-mode')
    ip_versions = ['ipv4', 'ipv6']
    context = {
        'title': 'IP Version',
        'data': ip_versions,
        'next': 'vnf-configuration'
    }
    return render(request, 'execute_test/list_reg.html', context=context)


def regression_mode(request):
    if request.session['vnf_type'] == 'all':
        return redirect('/execute_test/regression/priority')
    else:
        regression_mode = ['priority', 'testsuite']
        context = {
            'data': regression_mode,
            'title': 'Regression Mode'
        }
        return render(request, 'execute_test/list_reg.html', context=context)


def regression_priority(request):
    request.session['reg_mode'] = 'priority'
    form = RegressionPriorityForm(request.POST or None)
    if form.is_valid():
        request.session['priority'] = form.cleaned_data['priority']
        time.sleep(10)
        execute_regression_priority.delay(dict(request.session.items()),
                                          form.cleaned_data['priority'])
        return redirect('/execute_test/results')
    context = {
        'form': form,
    }
    return render(request, 'execute_test/priority_form.html', context=context)


def regression_config_vnf(request, ip_version):
    if request.method == 'GET':
        request.session['ip_version'] = ip_version
    form = VNFConfigForm(request.POST or None)
    if form.is_valid():
        request.session['lb_count'] = form.cleaned_data['lb_count']
        request.session['worker_threads'] = form.cleaned_data['worker_threads']
        request.session['worker_config'] = form.cleaned_data[
            'worker_configuration']
        lb_config = form.cleaned_data['lb_config']
        if lb_config == 'HW' and request.session[
                'deployment_type'] == 'baremetal':
            pod_data = yaml.safe_load(
                open('/etc/yardstick/nodes/pod.yaml', 'r').read())
            for interface in pod_data['nodes'][1]['interfaces']:
                if pod_data['nodes'][1]['interfaces'][interface][
                        'driver'].lower() != 'i40e':
                    lb_config = 'SW'
                    break
        else:
            lb_config = 'SW'
        request.session['lb_config'] = lb_config
        return redirect('/execute_test/regression/regression-mode')
    context = {
        'form': form,
        'ip': ip_version
    }
    print ip_version
    return render(
        request, 'execute_test/reg_vnf_config_form.html', context=context)


@task
def execute_regression_priority(request, priority):
    redis_publisher = RedisPublisher(facility='logging', broadcast=True)
    message = RedisMessage('Starting Regression')
    redis_publisher.publish_message(message)
    priority = int(priority)
    vnf_type = request['vnf_type']
    regression_type = request['regression_type']
    deployment_type = request['deployment_type']
    regression_mode = request['reg_mode']
    os.system("mkdir -p {0}/logs".format(gui_dir))
    os.system("mkdir -p {0}/results".format(gui_dir))
    exec_dir = '{0}/{1}'.format(deployment_type, regression_type)
    vnf_list = [request['vnf_type']
                ] if vnf_type != 'all' else request['vnf_types']
    with open('/tmp/regression.out', 'w') as reg_file:
        pass
    redis_publisher = RedisPublisher(facility='logging', broadcast=True)
    for vnf in vnf_list:
        execution_dir = os.path.join(
            test_cases_dir, '{0}/{1}'.format(vnf.lower(), exec_dir))
        try:
            os.chdir(execution_dir)
        except OSError:
            print "Exception Raised"
            print execution_dir
            continue
        if regression_type in non_performance_test_types:
            tc_list = filter(
                os.path.isfile, [
                    x for x in os.listdir('.') if x.startswith('tc')])
        else:
            ip_version = request['ip_version']
            tc_list = filter(
                os.path.isfile, [
                    x for x in os.listdir('.') if x.startswith('tc') and
                    ip_version in x])

        tmp_list = []
        for tc in tc_list:
            if priority != 0:
                with open(tc) as fh:
                    test_data = yaml.load(fh.read())
                if 'tc_options' in test_data['scenarios'][0]:
                    tc_priority = test_data['scenarios'][0][
                        'tc_options'].get('priority', 0)
                else:
                    tc_priority = 0
                if tc_priority == priority:
                    tmp_list.append(tc)
            else:
                tmp_list.append(tc)
        for tc in tmp_list:
            if vnf.lower() in ('acl', 'cgnat', 'firewall') and \
                    regression_type in performance_test_types:
                with open(tc) as fh:
                    test_data = yaml.safe_load(fh.read())
                vnf_config = {}
                vnf_config['worker_config'] = request['worker_config']
                vnf_config['lb_count'] = request['lb_count']
                vnf_config['lb_config'] = request['lb_config']
                vnf_config['worker_threads'] = request['worker_threads']
                if 'vnf_options' not in test_data['scenarios'][0]:
                    test_data['scenarios'][0]['vnf_options'] = {}
                test_data['scenarios'][0]['vnf_options'][
                    'vnf_config'] = vnf_config
                yaml.safe_dump(test_data, open(tc, 'w'))
            msg = 'Executing {0} in {1}'.format(tc, vnf)
            message = RedisMessage(msg)
            redis_publisher.publish_message(message)
            print "----------------- Executing {0} ---------------".format(tc)
            log_file = datetime.now().strftime(
                "{0}/logs/{1}_%d_%m_%Y_%H_%M_%S.log".format(gui_dir, tc))
            log_open = open(log_file, 'a')
            os.system("rm /tmp/yardstick.out > /dev/null 2>&1")
            command = 'yardstick --debug task start {0}'.format(tc)
            p = subprocess.Popen(
                command, shell=True, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            for line in iter(p.stdout.readline, ''):
                print line
                log_open.write(line)
            log_open.close()
            msg = 'Execution completed for {0} in {1}'.format(tc, vnf)
            message = RedisMessage(msg)
            redis_publisher.publish_message(message)
            if os.path.isfile("/tmp/yardstick.out") and \
                    regression_mode == 'priority':
                out = open("/tmp/yardstick.out")
                tmp = out.readlines()
                line = tmp.pop()
                tc_result = line
                if regression_type in performance_test_types:
                    tc = tc.split('_')
                    item_dict = {}
                    for item in tc:
                        if item.lower() in ('ipv4', 'ipv6'):
                            item_dict['ip_version'] = item.lower()
                        elif item.lower() in ('1flow', '1kflow', '16kflow',
                                              '256kflow', '1mflow'):
                            item_dict['flows'] = item.lower()
                        elif item.lower() in ('64b', '1518b', 'imix'):
                            item_dict['size'] = item.lower()
                        else:
                            pass
                    result = {
                        "throughput": tc_result['benchmark']['data']['tg__1'][
                            'Throughput'],
                        "drop_percentage": tc_result['benchmark']['data'][
                            'tg__1']['DropPercentage']
                    }
                    result.update(item_dict)
                elif regression_type == 'verification':
                    tg_2_data = tc_result['benchmark']['data']['tg__2']
                    result = 'PASS' if int(tg_2_data[
                        'Total packets verified']) == int(tg_2_data[
                        'Total packets match']) else 'FAIL'
                    result = {
                        'result': result
                    }

                elif regression_type in ('http_tests', 'attacker_tests'):
                    tg_1_data = tc_result['benchmark']['data']['tg__1']
                    result = 'PASS' if int(
                        tg_1_data["failed_requests"]) == 0 else 'FAIL'
                    result = {
                        'result': result
                    }

                else:
                    result = {
                        'result': tc_result['benchmark']['data']['vnf__1'].get(
                            'tg_test_result :', 'FAIL')
                    }
                shutil.copy(
                    "/tmp/yardstick.out", '{0}/results/{1}_{2}'.format(
                        gui_dir, vnf, tc))
            else:
                result = {
                    'result': 'FAIL'
                }
            stats = {'vnf': vnf, "test_case": tc}
            stats.update(result)
            with open('/tmp/regression.out', 'a') as reg_file:
                reg_file.write(json.dumps(stats) + '\n')
            message = RedisMessage(json.dumps(stats))
            redis_publisher.publish_message(message)
    message = RedisMessage('Regression Completed')
    redis_publisher.publish_message(message)
    os.chdir(gui_dir)


def regression_results(request):
    context = {}
    try:
        with open('/tmp/regression.out') as reg_file:
            reg_data = reg_file.readlines()
    except:
        return render(
            request, 'execute_test/regression_result.html', context=context)
    data = [line for line in reg_data]
    if "throughput" in data[0]:
        reg_type = 'performance'
        graph_data = {
            '64b': [['Flow Count', 'Throughput']],
            '1518b': [['Flow Count', 'Throughput']],
            'imix': [['Flow Count', 'Throughput']],
        }
        for line in data:
            if line['ip_version'] == 'ipv4':
                graph = [str(line['flows']), round(
                    float(line['throughput']) / 1000000, 2)]
                tmp = graph_data[line['size']]
                tmp.append(graph)
                graph_data[line['size']] = tmp
        context.update({'graph_data': json.dumps(graph_data)})
    else:
        reg_type = 'functional'
        context.update({
            'total_tc': len(data),
            'total_pass': sum([1 for x in data if x[
                'result'].lower() == 'pass']),
            'total_fail': sum([1 for x in data if x[
                'result'].lower() == 'fail'])
        })
    context.update({
        'data': data,
        'reg_type': reg_type
    })
    return render(
        request, 'execute_test/regression_result.html', context=context)


def scaleup_results(request):
    context = {}
    try:
        with open('/tmp/scaleup.out') as reg_file:
            reg_data = reg_file.readlines()
    except:
        return render(
            request, 'execute_test/scaleup_result.html', context=context)

    try:
        data = [line for line in reg_data]
    except:
        reg_data.pop(0)
        reg_data.pop(-1)
        data = [json.loads(line) for line in reg_data]
    graph_data = [['Throughput', 'Cores']]
    for index, line in enumerate(data, 1):
        tmp = []
        tmp.append(str(index))
        tmp.append(round(line['Throughput'] / 1000000, 2))
        graph_data.append(tmp)
    context = {
        'data': data,
        'graph_data':  json.dumps(graph_data)
    }
    return render(request, 'execute_test/scaleup_result.html', context=context)


def regression_testsuite(request, mode):
    request.session['reg_mode'] = 'testsuite'
    vnf_type = request.session['vnf_type']
    regression_type = request.session['regression_type']
    deployment_type = request.session['deployment_type']
    os.system("mkdir -p {0}/logs".format(gui_dir))
    os.system("mkdir -p {0}/results".format(gui_dir))
    exec_dir = '{0}/functional'.format(
        deployment_type) if regression_type == 'functional' else \
        '{0}/throughput'.format(deployment_type)
    os.chdir('{0}/{1}/{2}'.format(gui_dir, vnf_type, exec_dir))


@task
def execute_scaleup(request):
    vnf_type = request['vnf_type']
    deployment_type = request['deployment_type']
    test_type = 'throughput'
    test_case = request['test_case']
    no_worker_threads = request['worker_threads']
    lb_count = request['lb_count']
    worker_config = str(request['worker_config'])
    worker_threads = range(1, no_worker_threads + 1) if \
        worker_config == '1c/1t' else range(2, no_worker_threads + 1, 2)
    os.system("mkdir -p {0}/logs".format(gui_dir))
    out_results = {}
    throughput_dir = os.path.join(
        test_cases_dir, '{0}/{1}/{2}'.format(
            vnf_type, deployment_type, test_type))
    os.chdir(throughput_dir)
    scaleup_dir = os.path.join(
        test_cases_dir, '{0}/{1}/scaleup'.format(vnf_type, deployment_type))
    if not os.path.exists(scaleup_dir):
        os.mkdir(scaleup_dir)
    with open(test_case) as fh:
        tc_yaml = yaml.load(fh.read())
    topology_file = tc_yaml['scenarios'][0]['topology']
    shutil.copy(topology_file, scaleup_dir)
    shutil.copy(test_case, scaleup_dir)
    os.chdir(scaleup_dir)
    vnf_config = {}
    vnf_config['worker_config'] = worker_config
    vnf_config['lb_count'] = lb_count
    redis_publisher = RedisPublisher(facility='logging', broadcast=True)
    with open('/tmp/scaleup.out', 'w') as sfh:
        pass
    for worker_thread in worker_threads:
        vnf_config['worker_threads'] = worker_thread
        with open(test_case) as fh:
            tc_yaml = yaml.load(fh.read())
        if 'vnf_options' not in tc_yaml['scenarios'][0]:
            tc_yaml['scenarios'][0]['vnf_options'] = {}
        tc_yaml['scenarios'][0]['vnf_options']['vnf_config'] = vnf_config
        yaml.dump(tc_yaml, open(test_case, 'w'))
        log_file = datetime.now().strftime(
            "{0}/logs/{1}_%d_%m_%Y_%H_%M_%S.log".format(gui_dir, test_case))
        with open(log_file, 'w') as fh:
            pass
        log_open = open(log_file, 'a')
        os.system("rm /tmp/yardstick.out > /dev/null 2>&1")
        print '{0}/{1}'.format(os.getcwd(), test_case)
        msg = 'Executing {0} with {1} worker thread'.format(
            test_case, worker_thread)
        message = RedisMessage(msg)
        redis_publisher.publish_message(message)
        command = 'yardstick --debug task start {0}'.format(test_case)
        p = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, ''):
            print line
            log_open.write(line)
        log_open.close()
        msg = 'Execution completed for {0} with {1} worker thread'.format(
            test_case, worker_thread)
        message = RedisMessage(msg)
        redis_publisher.publish_message(message)
        tmp = ""
        if os.path.isfile("/tmp/yardstick.out"):
            out = open("/tmp/yardstick.out")
            tmp = out.readlines()
            line = tmp.pop(len(tmp) - 1)
            tc_result = json.loads(line)
            result_data = {
                "worker_threads": worker_thread,
                "worker_configuration": worker_config,
                "Throughput": tc_result["benchmark"]["data"]["tg__1"].get(
                    "Throughput", 0),
                "DropPercentage": tc_result["benchmark"]["data"]["tg__1"].get(
                    "DropPercentage", 100)}
            out_results[int(worker_thread)] = {
                "Throughput": tc_result["benchmark"]["data"]["tg__1"].get(
                    "Throughput", 0),
                "DropPercentage": tc_result["benchmark"]["data"]["tg__1"].get(
                    "DropPercentage", 100)}
            with open('/tmp/scaleup.out', 'a') as sfh:
                sfh.write(json.dumps(result_data) + '\n')
            message = RedisMessage(json.dumps(result_data))
            redis_publisher.publish_message(message)


def page_not_available(request):
    return render(request, 'execute_test/page_not_available.html', context={})
