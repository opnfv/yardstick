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

usage()
{
    cat <<EOF

Yardstick NSB setup script.

Usage: $0 [-h] [[-o] admin-openrc-for-openstack] [-i yardstick-docker-image]

Options:
 -h         Show this message and exit
 -o openrc  Specify admin-openrc file with OpenStack credentials
            Defaults to none
 -i image   Specify Yardstick Docker image, e.g. opnfv/yardstick:stable
            Default value provided by ansible/nsb_setup.yml
            See https://hub.docker.com/r/opnfv/yardstick/tags/

EOF
}

OPTSTR=':ho:i:'
openrc=
image=

# For backward compatibility reasons, accept openrc both as an argument
# and as the -o option. Hence these two loops.
while [ $# -ge 1 ]; do
    OPTIND=1
    while getopts ${OPTSTR} OPT; do
        case $OPT in
            h)
                usage
                exit 0
                ;;
            o)
                openrc=${OPTARG}
                ;;
            i)
                image=${OPTARG}
                ;;
            :)
                usage
                echo "ERROR: Missing value for -${OPTARG} option"
                exit 1
                ;;
            *)
                usage
                echo "ERROR: Invalid -${OPTARG} option"
                exit 1
                ;;
        esac
    done

    if [ ${OPTIND} -eq 1 ]; then
        openrc=$1
        shift
    else
        shift $((OPTIND - 1))
    fi
done

# OPENRC handling has to be first due no_proxy
if [ -n "${openrc}" ]; then
    OPENRC=$(readlink -f -- "${openrc}")
    extra_args="${extra_args} -e openrc_file=${OPENRC}"
    source "${OPENRC}"
    CONTROLLER_IP=$(echo ${OS_AUTH_URL} | sed -ne "s#http://\([0-9a-zA-Z.\-]*\):*[0-9]*/.*#\1#p")
fi

if [ -n "${image}" ]; then
    extra_args="${extra_args} -e yardstick_docker_image=${image}"
fi

env_http_proxy=$(sed -ne "s/^http_proxy=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
if [[ -z ${http_proxy} ]] && [[ ! -z ${env_http_proxy} ]]; then
    export http_proxy=${env_http_proxy}
fi
env_https_proxy=$(sed -ne "s/^https_proxy=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
if [[ -z ${https_proxy} ]] && [[ ! -z ${env_https_proxy} ]]; then
    export https_proxy=${env_https_proxy}
fi

# if http[s]_proxy is set (from env or /etc/environment) prepare proxy for ansible
if [[ ! -z ${http_proxy} ]] || [[ ! -z ${https_proxy} ]]; then
    export no_proxy="localhost,127.0.0.1,${CONTROLLER_IP},${no_proxy}"
    extra_args="${extra_args} -e @/tmp/proxy.yml "

    cat <<EOF > /tmp/proxy.yml
---
proxy_env:
  http_proxy: ${http_proxy}
  https_proxy: ${https_proxy}
  no_proxy: ${no_proxy}
EOF

    mkdir -p /etc/systemd/system/docker.service.d
    cat <<EOF > /etc/systemd/system/docker.service.d/http-proxy.conf
---
[Service]
Environment="HTTP_PROXY=${http_proxy}" "HTTPS_PROXY=${https_proxy}" "NO_PROXY=${no_proxy}"
EOF

    systemctl daemon-reload
    systemctl restart docker
fi

apt-get update > /dev/null 2>&1
pkg=(python-pip build-essential libssl-dev libffi-dev python3-dev python-dev)
for i in "${pkg[@]}"; do
    dpkg-query -W --showformat='${Status}\n' "${i}"|grep "install ok installed"
    if [  "$?" -eq "1" ]; then
        apt-get -y install "${i}";
    fi
done

pip install ansible==2.5.5 shade==1.22.2 docker-py==1.10.6

ANSIBLE_SCRIPTS="ansible"

cd ${ANSIBLE_SCRIPTS} &&\
ansible-playbook \
         -e img_property="nsb" \
         -e YARD_IMG_ARCH='amd64' ${extra_args}\
         -i install-inventory.ini nsb_setup.yml

