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
export YARD_IMG_ARCH

if ! grep -q "Defaults env_keep += \"YARD_IMG_ARCH\"" "/etc/sudoers"; then
    echo "Defaults env_keep += \"YARD_IMG_ARCH YARDSTICK_REPO_DIR\"" | sudo tee -a /etc/sudoers
fi

# Look for a compute node, that is online, and check if it is aarch64
ARCH_SCRIPT="ssh \$(fuel2 node list | awk -F'|' '\$6 ~ /compute/ && \$11 ~ /rue/ {print \$7; exit;}') uname -m 2>/dev/null | grep -q aarch64"
if [ "$INSTALLER_TYPE" == "fuel" ]; then
    sshpass -p r00tme ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -l root "${INSTALLER_IP}" "${ARCH_SCRIPT}" && YARD_IMG_ARCH=arm64
fi

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
            local cmd
            cmd="sudo $(which yardstick-img-modify) $(pwd)/tools/ubuntu-server-cloudimg-modify.sh"

            # Build the image. Retry once if the build fails
            $cmd || $cmd

            if [ ! -f "${QCOW_IMAGE}" ]; then
                echo "Failed building QCOW image"
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
    if [[ "${YARD_IMG_ARCH}" == "arm64" && "${YARD_IMG_AKI}" == "true" ]]; then
        CLOUD_IMAGE="/tmp/${release}-server-cloudimg-${YARD_IMG_ARCH}.tar.gz"
        CLOUD_KERNEL="/tmp/${release}-server-cloudimg-${YARD_IMG_ARCH}-vmlinuz-generic"
        cd /tmp
        if [ ! -f "${CLOUD_IMAGE}" ]; then
            wget "${CLOUD_IMG_URL}"
        fi
        if [ ! -f "${CLOUD_KERNEL}" ]; then
            tar xf "${CLOUD_IMAGE}" "${CLOUD_KERNEL##**/}"
        fi
        create_kernel=$(openstack ${SECURE} image create \
                --public \
                --disk-format qcow2 \
                --container-format bare \
                --file ${CLOUD_KERNEL} \
                yardstick-${release}-kernel)

        GLANCE_KERNEL_ID=$(echo "$create_kernel" | awk '/ id / {print $(NF-1)}')
        if [ -z "$GLANCE_KERNEL_ID" ]; then
            echo 'Failed uploading kernel to cloud'.
            exit 1
        fi

        command_line="root=/dev/vdb1 console=tty0 console=ttyS0 console=ttyAMA0 rw"

        EXTRA_PARAMS="--property kernel_id=$GLANCE_KERNEL_ID --property os_command_line=\"$command_line\""

        rm -f -- "${CLOUD_KERNEL}" "${CLOUD_IMAGE}"
        cd "${YARDSTICK_REPO_DIR}"
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
    if [[ "${YARD_IMG_ARCH}" == "arm64" ]]; then
        CIRROS_IMAGE_VERSION="cirros-d161201"
        CIRROS_IMAGE_PATH="/home/opnfv/images/cirros-d161201-aarch64-disk.img"
    else
        CIRROS_IMAGE_VERSION="Cirros-0.3.5"
        CIRROS_IMAGE_PATH="/home/opnfv/images/cirros-0.3.5-x86_64-disk.img"
    fi

    if [[ -n $(openstack ${SECURE} image list | grep -e "${CIRROS_IMAGE_VERSION}") ]]; then
        echo "${CIRROS_IMAGE_VERSION} image already exist, skip loading cirros image"
    else
        echo
        echo "========== Loading cirros cloud image =========="

        local image_file="${CIRROS_IMAGE_PATH}"

        EXTRA_PARAMS=""
        # VPP requires guest memory to be backed by large pages
        if [[ "$DEPLOY_SCENARIO" == *"-fdio-"* ]]; then
            EXTRA_PARAMS=$EXTRA_PARAMS" --property hw_mem_page_size=large"
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
        openstack ${SECURE} flavor create --id 100 --ram 1024 --disk 3 --vcpus 1 yardstick-flavor
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
        sed -i 's/image: {{image}}/image: TestVM/g' tests/opnfv/test_cases/opnfv_yardstick_tc002.yaml
        sed -i 's/image: cirros-0.3.5/image: TestVM/g' samples/ping.yaml
        #We have overlapping IP with the real network
        for filename in tests/opnfv/test_cases/*; do
            sed -i "s/cidr: '10.0.1.0\/24'/cidr: '10.3.1.0\/24'/g" "${filename}"
        done
    else
        load_cirros_image
        load_ubuntu_image
    fi
    create_nova_flavor
}

main
