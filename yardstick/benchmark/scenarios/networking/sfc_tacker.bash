#!/bin/bash
BASEDIR=`pwd`

#import VNF descriptor
tacker vnfd-create --vnfd-file ${BASEDIR}/test-vnfd.yaml

#create instances of the imported VNF
tacker vnf-create --name testVNF1 --vnfd-name test-vnfd
tacker vnf-create --name testVNF2 --vnfd-name test-vnfd

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
tacker sfc-create --name chainA --chain testVNF1
tacker sfc-create --name chainB --chain testVNF2

#create classifier
tacker sfc-classifier-create --name myclassA --chain chainA --match source_port=0,dest_port=80,protocol=6
tacker sfc-classifier-create --name myclassB --chain chainB --match source_port=0,dest_port=22,protocol=6

tacker sfc-list
tacker sfc-classifier-list
