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

#pip install ansible==2.3.2 shade==1.17.0

ANSIBLE_SCRIPTS="../ansible"

cd $(dirname $0)
cd ${ANSIBLE_SCRIPTS} &&\
ansible-playbook \
         -i ../ansible/virt_ci_hosts.ini check_rs.yml
