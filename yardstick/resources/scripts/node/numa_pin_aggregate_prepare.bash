#!/bin/bash

##############################################################################
# Copyright (c) 2017 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

prepare_aggregate_flavor()
{
    # Create the "pinned-cpu" aggregate for hosts that will received pinning
    # requests.

    nova aggregate-create pinned-cpu
    # openstack aggregate create pinned-cpu

    # Create the "regular" aggregate for all other hosts

    nova aggregate-create regular
    # openstack aggregate create regular

    # Set metadata on the "pinned-cpu" aggregate, this will be used to match the
    # flavor we create shortly - here we are using the arbitrary key pinned and
    # setting it to true.

    nova aggregate-set-metadata pinned-cpu pinned=true
    # openstack aggregate set --property pinned=true pinned-cpu

    # Set metadata on the "regular" aggregate, this will be used to match all
    # existing "regular" flavors - here we are using the same key as before and
    # setting it to false.

    nova aggregate-set-metadata regular pinned=false
    # openstack aggregate set --property pinned=false regular

    # Add the existing compute nodes to the corresponding Nova aggregates.
    # Hosts that are not intended to be targets for pinned instances should be
    # added to the "regular" host aggregate

    compute_nodes=($(nova host-list | grep compute | sort | awk '{print $2}'))
    # compute_nodes=($(openstack availability zone list --long | grep nova-compute | sort | awk '{print $7}'))

    nova aggregate-add-host pinned-cpu ${compute_nodes[0]}
    # openstack aggregate add host pinned-cpu ${compute_nodes[0]}

    nova aggregate-add-host regular ${compute_nodes[1]}
    # openstack aggregate add host regular ${compute_nodes[1]}

    # Before creating the new flavor for cpu-pinning instances update all existing
    # flavors so that their extra specifications match them to the compute hosts in
    # the "regular" aggregate:

    for FLAVOR in `nova flavor-list | grep "True" | cut -f 2 -d ' '`; \
        do nova flavor-key ${FLAVOR} set \
            aggregate_instance_extra_specs:pinned=false; \
        done

    #for FLAVOR in `nova flavor-list | grep "True" | cut -f 2 -d ' '`; \
    #    do openstack flavor set --property \
    #        aggregate_instance_extra_specs:pinned=false ${FLAVOR}; \
    #    done

    # Create a new flavor "yardstick-pinned-flavor" for CPU pinning.
    # Set the hw:cpy_policy flavor extraspecification to dedicated. This denotes
    # that allinstances created using this flavor will require dedicated compute
    # resources and be pinned accordingly.
    # Set the aggregate_instance_extra_specs:pinned flavor extra specification to
    # true. This denotes that all instances created using this flavor will be sent
    # to hosts in host aggregates with pinned=true in their aggregate metadata:

    nova flavor-create yardstick-pinned-flavor 101 512 3 2
    #openstack flavor create --id 101 --ram 512 --disk 3 --vcpus 2 yardstick-pinned-flavor

    # To restrict an instance’s vCPUs to a single host NUMA node
    nova flavor-key yardstick-pinned-flavor set hw:numa_nodes=1
    # openstack flavor set --property hw:numa_nodes=1 yardstick-pinned-flavor

    nova flavor-key yardstick-pinned-flavor set hw:cpu_policy=dedicated
    # openstack flavor set --property hw:cpu_policy=dedicated yardstick-pinned-flavor

    nova flavor-key yardstick-pinned-flavor set aggregate_instance_extra_specs:pinned=true
    # openstack flavor set --property aggregate_instance_extra_specs:pinned=true yardstick-pinned-flavor
}

prepare_aggregate_flavor
