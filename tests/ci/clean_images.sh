#!/bin/bash
##############################################################################
# Copyright (c) 2015 Ericsson AB, Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Clean the images and flavor before running yardstick test suites.

cleanup()
{
    echo
    echo "========== Cleanup =========="

    if ! openstack image list; then
        return
    fi

    for image in $(openstack image list | grep -e cirros-0.3.5 -e yardstick-image -e Ubuntu-16.04 \
        | awk '{print $2}'); do
        echo "Deleting image $image..."
        openstack image delete $image || true
    done

    openstack flavor delete yardstick-flavor &> /dev/null || true
    openstack flavor delete storperf &> /dev/null || true
}

main()
{
    cleanup
}

main
