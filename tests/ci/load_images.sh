#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB, Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Set up the environment to run yardstick test suites.

set -e

YARD_IMG_ARCH=amd64

if ! grep -q "Defaults env_keep += \"YARD_IMG_ARCH\"" "/etc/sudoers"; then
    echo "Defaults env_keep += \"YARD_IMG_ARCH YARDSTICK_REPO_DIR\"" | sudo tee -a /etc/sudoers
fi

# Look for a compute node, that is online, and check if it is aarch64
if [ "${INSTALLER_TYPE}" == 'fuel' ]; then
    ssh_options="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
    COMPUTE_ARCH=$(ssh -l ubuntu ${INSTALLER_IP} -i ${SSH_KEY} ${ssh_options} \
        "sudo salt 'cmp*' grains.get cpuarch --out yaml | awk '{print \$2; exit}'")
    if [ "${COMPUTE_ARCH}" == 'aarch64' ]; then
        YARD_IMG_ARCH=arm64
    fi
fi
export YARD_IMG_ARCH

HW_FW_TYPE=""
if [ "${YARD_IMG_ARCH}" == "arm64" ]; then
    HW_FW_TYPE=uefi
fi
export HW_FW_TYPE

UCA_HOST="cloud-images.ubuntu.com"
if [ "${YARD_IMG_ARCH}" == "arm64" ]; then
    export CLOUD_IMG_URL="http://${UCA_HOST}/${release}/current/${release}-server-cloudimg-${YARD_IMG_ARCH}.tar.gz"
    if ! grep -q "Defaults env_keep += \"CLOUD_IMG_URL\"" "/etc/sudoers"; then
        echo "Defaults env_keep += \"CLOUD_IMG_URL\"" | sudo tee -a /etc/sudoers
    fi
fi

build_yardstick_image()
{
    echo
    echo "========== Build yardstick cloud image =========="

    if [[ "$DEPLOY_SCENARIO" == *"-lxd-"* ]]; then
        if [ ! -f "${RAW_IMAGE}" ];then
            local cmd
            cmd="sudo $(which yardstick-img-lxd-modify) $(pwd)/tools/ubuntu-server-cloudimg-modify.sh"

            # Build the image. Retry once if the build fails
            $cmd || $cmd

            if [ ! -f "${RAW_IMAGE}" ]; then
                echo "Failed building RAW image"
                exit 1
            fi
        fi
    else
        if [ ! -f "${QCOW_IMAGE}" ];then
            ANSIBLE_SCRIPTS="${0%/*}/../../ansible"
            cd ${ANSIBLE_SCRIPTS} &&\
            ansible-playbook \
                     -e img_property="normal" \
                     -e YARD_IMG_ARCH=${YARD_IMG_ARCH} \
                     -vvv -i inventory.ini build_yardstick_image.yml

            if [ ! -f "${QCOW_IMAGE}" ]; then
                echo "Failed building QCOW image"
                exit 1
            fi
        fi
        # DPDK compile is not enabled for arm64 yet so disable for now
        # JIRA: YARSTICK-1124
        if [[ ! -f "${QCOW_NSB_IMAGE}"  && ${DEPLOY_SCENARIO} == *[_-]ovs[_-]* && "${YARD_IMG_ARCH}" != "arm64" ]]; then
            ansible-playbook \
                     -e img_property="nsb" \
                     -e YARD_IMG_ARCH=${YARD_IMG_ARCH} \
                     -vvv -i inventory.ini build_yardstick_image.yml
            if [ ! -f "${QCOW_NSB_IMAGE}" ]; then
                echo "Failed building QCOW NSB image"
                exit 1
            fi
        fi
    fi
}

load_yardstick_image()
{
    echo
    echo "========== Loading yardstick cloud image =========="
    EXTRA_PARAMS=""
    if [[ "${YARD_IMG_ARCH}" == "arm64" ]]; then
        EXTRA_PARAMS="--property hw_video_model=vga"
    fi

    # VPP requires guest memory to be backed by large pages
    if [[ "$DEPLOY_SCENARIO" == *"-fdio-"* ]]; then
        EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_mem_page_size=large"
    fi

    if [[ -n "${HW_FW_TYPE}" ]]; then
        EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_firmware_type=${HW_FW_TYPE}"
    fi

    if [[ "$DEPLOY_SCENARIO" == *"-lxd-"* ]]; then
        output=$(eval openstack ${SECURE} image create \
            --public \
            --disk-format raw \
            --container-format bare \
            ${EXTRA_PARAMS} \
            --file ${RAW_IMAGE} \
            yardstick-image)
    else
        output=$(eval openstack ${SECURE} image create \
            --public \
            --disk-format qcow2 \
            --container-format bare \
            ${EXTRA_PARAMS} \
            --file ${QCOW_IMAGE} \
            yardstick-image)
        if [[ $DEPLOY_SCENARIO == *[_-]ovs[_-]* ]]; then
            nsb_output=$(eval openstack ${SECURE} image create \
                --public \
                --disk-format qcow2 \
                --container-format bare \
                ${EXTRA_PARAMS} \
                --file ${QCOW_NSB_IMAGE} \
                yardstick-samplevnfs)
            echo "$nsb_output"
        fi
    fi

    echo "$output"

    GLANCE_IMAGE_ID=$(echo "$output" | grep " id " | awk '{print $(NF-1)}')

    if [ -z "$GLANCE_IMAGE_ID" ]; then
        echo 'Failed uploading image to cloud'.
        exit 1
    fi

    echo "Glance image id: $GLANCE_IMAGE_ID"
}

load_cirros_image()
{
    EXTRA_PARAMS=""
    if [[ "${YARD_IMG_ARCH}" == "arm64" ]]; then
        CIRROS_IMAGE_VERSION="cirros-d161201"
        CIRROS_IMAGE_PATH="/home/opnfv/images/cirros-d161201-aarch64-disk.img"
        EXTRA_PARAMS="--property hw_video_model=vga --property short_id=ubuntu16.04"
    else
        CIRROS_IMAGE_VERSION="cirros-0.3.5"
        CIRROS_IMAGE_PATH="/home/opnfv/images/cirros-0.3.5-x86_64-disk.img"
    fi

    if [[ -n $(openstack ${SECURE} image list | grep -e "${CIRROS_IMAGE_VERSION}") ]]; then
        echo "${CIRROS_IMAGE_VERSION} image already exist, skip loading cirros image"
    else
        echo
        echo "========== Loading cirros cloud image =========="

        local image_file="${CIRROS_IMAGE_PATH}"

        # VPP requires guest memory to be backed by large pages
        if [[ "$DEPLOY_SCENARIO" == *"-fdio-"* ]]; then
            EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_mem_page_size=large"
        fi

        if [[ -n "${HW_FW_TYPE}" ]]; then
            EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_firmware_type=${HW_FW_TYPE}"
        fi

        output=$(openstack ${SECURE} image create \
            --disk-format qcow2 \
            --container-format bare \
            ${EXTRA_PARAMS} \
            --file ${image_file} \
            cirros-0.3.5)
        echo "$output"

        CIRROS_IMAGE_ID=$(echo "$output" | grep " id " | awk '{print $(NF-1)}')
        if [ -z "$CIRROS_IMAGE_ID" ]; then
            echo 'Failed uploading cirros image to cloud'.
            exit 1
        fi

        echo "Cirros image id: $CIRROS_IMAGE_ID"
    fi
}

load_ubuntu_image()
{
    echo
    echo "========== Loading ubuntu cloud image =========="

    local ubuntu_image_file=/home/opnfv/images/xenial-server-cloudimg-amd64-disk1.img

    EXTRA_PARAMS=""
    # VPP requires guest memory to be backed by large pages
    if [[ "$DEPLOY_SCENARIO" == *"-fdio-"* ]]; then
        EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_mem_page_size=large"
    fi

    output=$(openstack ${SECURE} image create \
        --disk-format qcow2 \
        --container-format bare \
        $EXTRA_PARAMS \
        --file $ubuntu_image_file \
        Ubuntu-16.04)
    echo "$output"

    UBUNTU_IMAGE_ID=$(echo "$output" | grep " id " | awk '{print $(NF-1)}')

    if [ -z "$UBUNTU_IMAGE_ID" ]; then
        echo 'Failed uploading UBUNTU image to cloud'.
        exit 1
    fi

    echo "Ubuntu image id: $UBUNTU_IMAGE_ID"
}

create_nova_flavor()
{
    if ! openstack ${SECURE} flavor list | grep -q yardstick-flavor; then
        echo
        echo "========== Creating yardstick-flavor =========="
        # Create the nova flavor used by some sample test cases
        openstack ${SECURE} flavor create --id 100 --ram 1024 --disk 10 --vcpus 1 yardstick-flavor
        # DPDK-enabled OVS requires guest memory to be backed by large pages
        if [[ $DEPLOY_SCENARIO == *[_-]ovs[_-]* ]]; then
            openstack ${SECURE} flavor set --property hw:mem_page_size=large yardstick-flavor
        fi
        # VPP requires guest memory to be backed by large pages
        if [[ "$DEPLOY_SCENARIO" == *"-fdio-"* ]]; then
            openstack ${SECURE} flavor set --property hw:mem_page_size=large yardstick-flavor
        fi
    fi

    if ! openstack ${SECURE} flavor list | grep -q storperf; then
        echo
        echo "========== Creating storperf flavor =========="
        # Create the nova flavor used by storperf test case
        openstack ${SECURE} flavor create --id auto --ram 8192 --disk 4 --vcpus 2 storperf
    fi
}

main()
{
    QCOW_IMAGE="/tmp/workspace/yardstick/yardstick-image.img"
    QCOW_NSB_IMAGE="/tmp/workspace/yardstick/yardstick-nsb-image.img"
    RAW_IMAGE="/tmp/workspace/yardstick/yardstick-image.tar.gz"

    if [ -f /home/opnfv/images/yardstick-image.img ];then
        QCOW_IMAGE='/home/opnfv/images/yardstick-image.img'
    fi
    if [ -f /home/opnfv/images/yardstick-image.tar.gz ];then
        RAW_IMAGE='/home/opnfv/images/yardstick-image.tar.gz'
    fi

    if [ $OS_INSECURE ] && [ "$(echo $OS_INSECURE | tr '[:upper:]' '[:lower:]')" = "true" ]; then
        SECURE="--insecure"
    else
        SECURE=""
    fi

    build_yardstick_image
    load_yardstick_image
    if [ "${YARD_IMG_ARCH}" == "arm64" ]; then
        #We have overlapping IP with the real network
        for filename in ${YARDSTICK_REPO_DIR}/tests/opnfv/test_cases/*; do
            sed -i "s/cidr: '10.0.1.0\/24'/cidr: '10.3.1.0\/24'/g" "${filename}"
        done
    else
        load_ubuntu_image
    fi
    load_cirros_image
    create_nova_flavor
}

main
