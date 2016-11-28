#!/bin/bash

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
