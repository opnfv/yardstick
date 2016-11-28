from yardstick.common.httpClient import HttpClient


class EnvCommand(object):

    def do_influxdb(self, args):
        url = 'http://localhost:5000/yardstick/env/action'
        data = {'action': 'createInfluxDBContainer'}
        HttpClient().post(url, data)
