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
rabbitmq_config='/etc/supervisor/conf.d/rabbitmq.conf'

if [[ ! -e "${supervisor_config}" ]]; then

    cat << EOF > "${supervisor_config}"
[supervisord]
nodaemon = true

[program:nginx]
command = service nginx restart

[program:yardstick_uwsgi]
directory = /etc/yardstick
command = uwsgi -i yardstick.ini
EOF

fi

if [[ ! -e "${rabbitmq_config}" ]]; then

    cat << EOF > "${rabbitmq_config}"
[program:rabbitmq]
command = /bin/bash -c "service rabbitmq-server restart && rabbitmqctl start_app && rabbitmqctl add_user yardstick yardstick && rabbitmqctl set_permissions -p / yardstick '.*' '.*' '.*'"
stdout_logfile=/var/log/rabbitmq_out.log
stderr_logfile=/var/log/rabbitmq_err.log
EOF

fi
