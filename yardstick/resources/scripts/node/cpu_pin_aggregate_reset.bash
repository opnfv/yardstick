#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

reset_aggregate_flavor()
{
    # Delete the "yardstick-pinned-flavor" flavor

    nova flavor-delete yardstick-pinned-flavor
    # openstack flavor delete yardstick-pinned-flavor

    # Unset the "aggregate_instance_extra_specs:pinned" property on all existing flavors

    for FLAVOR in `nova flavor-list | grep "True" | cut -f 2 -d ' '`; \
        do nova flavor-key ${FLAVOR} unset \
            aggregate_instance_extra_specs:pinned; \
        done

    #for FLAVOR in `nova flavor-list | grep "True" | cut -f 2 -d ' '`; \
    #    do openstack flavor unset --property \
    #        aggregate_instance_extra_specs:pinned ${FLAVOR}; \
    #    done

    # remove hosts from corresponding Nova aggregates

    compute_nodes=($(nova host-list | grep compute | sort | awk '{print $2}'))
    # compute_nodes=($(openstack availability zone list --long | grep nova-compute | sort | awk '{print $7}'))

    nova aggregate-remove-host pinned-cpu ${compute_nodes[0]}
    # openstack aggregate remove host pinned-cpu ${compute_nodes[0]}

    nova aggregate-remove-host regular ${compute_nodes[1]}
    # openstack aggregate remove host regular ${compute_nodes[1]}

    # Delete created Nova aggregates
    nova aggregate-delete pinned-cpu
    # openstack aggregate delete pinned-cpu

    nova aggregate-delete regular
    # openstack aggregate delete regular
}

reset_aggregate_flavor
