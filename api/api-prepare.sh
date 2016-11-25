#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# yardstick output config
output_config='/etc/yardstick/yardstick.conf'

if [[ ! -e "${output_config}" ]];then
    gateway_ip=$(ip route | grep default | awk '{print $3}')
    echo "${gateway_ip}"

    install -d /etc/yardstick -m 0755 -o root

    cat << EOF > "${output_config}"
[DEFAULT]
debug = True
dispatcher = influxdb

[dispatcher_file]
file_path = /tmp/yardstick.out

[dispatcher_http]
timeout = 5
# target = http://127.0.0.1:8000/results

[dispatcher_influxdb]
timeout = 5
target = http://${gateway_ip}:8086
db_name = yardstick
username = root
password = root
EOF
fi

# nginx config
nginx_config='/etc/nginx/conf.d/yardstick.conf'

if [[ ! -e "${nginx_config}" ]];then

    cat << EOF >> "${nginx_config}"
server {
    listen 5000;
    server_name localhost;
    index  index.htm index.html;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:///home/opnfv/repos/yardstick/api/yardstick.sock;
    }
}
EOF
fi

# nginx service start when boot
cat << EOF >> /root/.bashrc

nginx_status=\$(service nginx status | grep not)
if [ -n "\${nginx_status}" ];then
    service nginx restart
    uwsgi -i /home/opnfv/repos/yardstick/api/yardstick.ini
fi
EOF
