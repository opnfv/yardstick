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

    if ! glance image-list; then
        return
    fi

    for image in $(glance image-list | grep -e cirros-0.3.3 -e yardstick-trusty-server -e Ubuntu-14.04 \
        -e yardstick-vivid-kernel | awk '{print $2}'); do
        echo "Deleting image $image..."
        glance image-delete $image || true
    done

    nova flavor-delete yardstick-flavor &> /dev/null || true
}
