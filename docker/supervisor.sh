#!/bin/bash
##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# nginx service start when boot
supervisor_config='/etc/supervisor/conf.d/yardstick.conf'

if [[ ! -e "${supervisor_config}" ]]; then
    cat << EOF > "${supervisor_config}"
[supervisord]
nodaemon = true

[program:nginx]
command = service nginx restart

[program:yardstick_uwsgi]
directory = /etc/yardstick
command = uwsgi -i yardstick.ini

[program:rabbitmq]
command = service rabbitmq-server restart
EOF
fi
