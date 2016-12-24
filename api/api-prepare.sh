#!/bin/bash
##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# nginx config
nginx_config='/etc/nginx/conf.d/yardstick.conf'

if [[ ! -e "${nginx_config}" ]];then

    cat << EOF > "${nginx_config}"
server {
    listen 5000;
    server_name localhost;
    index  index.htm index.html;
    location / {
        include uwsgi_params;
        uwsgi_pass unix:///var/run/yardstick.sock;
    }
}
EOF
echo "daemon off;" >> /etc/nginx/nginx.conf
fi

# nginx service start when boot
supervisor_config='/etc/supervisor/conf.d/yardstick.conf'

if [[ ! -e "${supervisor_config}" ]];then
    cat << EOF > "${supervisor_config}"
[supervisord]
nodaemon = true

[program:yardstick_nginx]
user = root
command = service nginx restart
autorestart = true

[program:yardstick_uwsgi]
user = root
directory = /home/opnfv/repos/yardstick/api
command = uwsgi -i yardstick.ini
autorestart = true
EOF
fi

# create api log directory
mkdir -p /var/log/yardstick

# create yardstick.sock for communicating
touch /var/run/yardstick.sock
