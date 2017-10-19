#!/usr/bin/env bash
# Copyright (c) 2017 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

apt-get update > /dev/null 2>&1
pkg=(python-pip build-essential libssl-dev libffi-dev python3-dev python-dev)
for i in "${pkg[@]}"; do
    dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
    if [  "$?" -eq "1" ]; then
        apt-get -y install "${i}";
    fi
done

pip install ansible==2.3.2 shade==1.17.0 docker-py==1.10.6

if [ $# -eq 1 ]; then
    OPENRC=$(readlink -f -- "$1")
    extra_args="-e openrc_file=${OPENRC}"
    source "${OPENRC}"
    CONTROLLER_IP=$(echo ${OS_AUTH_URL} | sed -ne "s/http:\/\/\(.*\):.*/\1/p")
    export no_proxy="localhost,127.0.0.1,${CONTROLLER_IP},$no_proxy"
fi

if [ "$http_proxy" != "" ] || [ "$https_proxy" != "" ]; then
    extra_args="${extra_args} -e @/tmp/proxy.yml"

    cat <<EOF > /tmp/proxy.yml
---
proxy_env:
  http_proxy: $http_proxy
  https_proxy: $https_proxy
  no_proxy: $no_proxy
EOF
fi

ANSIBLE_SCRIPTS="ansible"

cd ${ANSIBLE_SCRIPTS} &&\
ansible-playbook \
         -e img_modify_playbook='ubuntu_server_cloudimg_modify_samplevnfs.yml' \
         -e YARD_IMG_ARCH='amd64' ${extra_args}\
         -i yardstick-install-inventory.ini nsb_setup.yml
