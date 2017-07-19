#!/bin/bash
##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

: ${YARDSTICK_REPO_DIR:='/home/opnfv/repos/yardstick'}

# generate uwsgi config file
mkdir -p /etc/yardstick
uwsgi_config='/etc/yardstick/yardstick.ini'
if [[ ! -e "${uwsgi_config}" ]];then

    cat << EOF > "${uwsgi_config}"
[uwsgi]
master = true
debug = true
chdir = ${YARDSTICK_REPO_DIR}/api
module = server
plugins = python
processes = 10
threads = 5
async = true
max-requests = 5000
chmod-socket = 666
callable = app_wrapper
enable-threads = true
close-on-exec = 1
daemonize= /var/log/yardstick/uwsgi.log
socket = /var/run/yardstick.sock
EOF
    if [[ "${YARDSTICK_VENV}" ]];then
        echo "virtualenv = ${YARDSTICK_VENV}" >> "${uwsgi_config}"
    fi
fi

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
directory = /etc/yardstick
command = uwsgi -i yardstick.ini
autorestart = true
EOF
fi

# create api log directory
mkdir -p /var/log/yardstick

# create yardstick.sock for communicating
touch /var/run/yardstick.sock

cp "${YARDSTICK_REPO_DIR}/etc/yardstick/yardstick.conf.sample" /etc/yardstick/yardstick.conf
