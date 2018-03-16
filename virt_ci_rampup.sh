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

env_http_proxy=$(sed -ne "s/^http_proxy=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
if [[ -z ${http_proxy} ]] && [[ ! -z ${env_http_proxy} ]]; then
    export http_proxy=${env_http_proxy}
fi
env_https_proxy=$(sed -ne "s/^https_proxy=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
if [[ -z ${https_proxy} ]] && [[ ! -z ${env_https_proxy} ]]; then
    export https_proxy=${env_https_proxy}
fi
env_ftp_proxy=$(sed -ne "s/^ftp_proxy=[\"\']\(.*\)[\"\']/\1/p" /etc/environment)
if [[ -z ${ftp_proxy} ]] && [[ ! -z ${env_ftp_proxy} ]]; then
    export ftp_proxy=${env_ftp_proxy}
fi
if [[ ! -z ${http_proxy} ]] || [[ ! -z ${https_proxy} ]]; then
    export no_proxy="${no_proxy}"
    extra_args="${extra_args} -e @/tmp/proxy.yml "
    cat <<EOF > /tmp/proxy.yml
---
proxy_env:
  http_proxy: ${http_proxy}
  https_proxy: ${https_proxy}
  ftp_proxy: ${ftp_proxy}
  no_proxy: ${no_proxy}
EOF
fi
#pip install ansible==2.3.2 shade==1.17.0 docker-py==1.10.6
ANSIBLE_SCRIPTS="${0%/*}/../ansible"

cd ${ANSIBLE_SCRIPTS} &&\
sudo -EH ansible-playbook \
         -e rs_file='../etc/infra/infra_deploy_two.yaml' ${extra_args} \
         -i inventory.ini infra_deploy.yml -vvvv
