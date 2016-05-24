#!/bin/bash
#set -e

#delete classifier
tacker sfc-classifier-delete myclassA
tacker sfc-classifier-delete myclassB

#delete service chain
tacker sfc-delete chainA
tacker sfc-delete chainB

#delete VNFs
tacker vnf-delete testVNF1
tacker vnf-delete testVNF2

#delete VNF descriptor
tacker vnfd-delete test-vnfd
