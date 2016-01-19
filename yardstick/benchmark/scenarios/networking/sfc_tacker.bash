#!/bin/bash
set -e
BASEDIR= `pwd`

#import VNF descriptor
tacker vnfd-create --vnfd-file ${BASEDIR}/test-vnfd.yaml

#create instances of the imported VNF
tacker vnf-create --name testVNF1 --vnfd-name test-vnfd
tacker vnf-create --name testVNF2 --vnfd-name test-vnfd

#create service chain
tacker sfc-create --name chainA --chain testVNF1
tacker sfc-create --name chainB --chain testVNF2

#create classifier
tacker sfc-classifier-create --name myclassA --chain chainA --match dest_port=80,protocol=6
tacker sfc-classifier-create --name myclassB --chain chainB --match dest_port=22,protocol=6

