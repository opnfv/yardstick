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

OPENRC='/home/opnfv/openrc'
source "${OPENRC}"
CONTROLLER_IP=$(echo ${OS_AUTH_URL} | sed -ne "s/http:\/\/\(.*\):.*/\1/p")
export no_proxy="localhost,${CONTROLLER_IP}"
ANSIBLE_SCRIPTS="${0%/*}/../../ansible"

cd ${ANSIBLE_SCRIPTS} &&\
ansible-playbook \
         -e img_modify_playbook='ubuntu_server_cloudimg_modify.yml' \
         -e target_os='Ubuntu' \
         -e YARD_IMG_ARCH='amd64' \
         -vvv -i inventory.ini load_images.yml
