#!/bin/bash
set -e

#delete classifier
tacker sfc-classifier-create myclassA
tacker sfc-classifier-create myclassB

#delete service chain
tacker sfc-delete chainA
tacker sfc-delete chainB

#delete VNFs
tacker vnf-delete testVNF1
tacker vnf-delete testVNF2

#delete VNF descriptor
tacker vnfd-delete test-vnfd
