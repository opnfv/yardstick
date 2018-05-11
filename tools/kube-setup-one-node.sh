#!/usr/bin/env bash
# Copyright (c) 2018 Intel Corporation.
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

proxy_vars=(http_proxy https_proxy ftp_proxy no_proxy)
# get proxy environment values from /etc/environment if not set
for proxy_var in ${proxy_vars[@]}
do
    env_proxy=$(sed -ne "s/^$proxy_var=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
    if [[ -z ${!proxy_var} ]] && [[ ! -z ${env_proxy} ]]; then
        export ${proxy_var}=${env_proxy}
    fi
done
# add proxy configuration into proxy file
add_extra_env=false
echo "proxy_env:" > /tmp/proxy.yml
for proxy_var in ${proxy_vars[@]}
do
    if [[ ! -z ${!proxy_var} ]]; then
        echo "  ${proxy_var}: ${!proxy_var}" >> /tmp/proxy.yml
        add_extra_env=true
    fi
done
# add extra arguments file if needed
if ${add_extra_env}; then
    extra_args="${extra_args} -e @/tmp/proxy.yml "
fi

ANSIBLE_SCRIPTS="${0%/*}/../ansible"

cd ${ANSIBLE_SCRIPTS} && \
ansible-playbook \
         ${extra_args} -i kube-inventory.ini deploy_kube.yml
