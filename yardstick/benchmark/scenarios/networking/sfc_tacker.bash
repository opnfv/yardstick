#!/bin/bash
##############################################################################
# Copyright (c) 2017 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

BASEDIR=`pwd`

#import VNF descriptor
tacker vnfd-create --vnfd-file ${BASEDIR}/test-vnfd1.yaml
tacker vnfd-create --vnfd-file ${BASEDIR}/test-vnfd2.yaml

#create instances of the imported VNF
tacker vnf-create --name testVNF1 --vnfd-name test-vnfd1
tacker vnf-create --name testVNF2 --vnfd-name test-vnfd2

key=true
while $key;do
        sleep 3
        active=`tacker vnf-list | grep -E 'PENDING|ERROR'`
        echo -e "checking if SFs are up:  $active"
        if [ -z "$active" ]; then
                key=false
        fi
done

#create service chain
tacker sfc-create --name red --chain testVNF1
tacker sfc-create --name blue --chain testVNF2

#create classifier
tacker sfc-classifier-create --name red_http --chain red --match source_port=0,dest_port=80,protocol=6
tacker sfc-classifier-create --name red_ssh --chain red --match source_port=0,dest_port=22,protocol=6

tacker sfc-list
tacker sfc-classifier-list
