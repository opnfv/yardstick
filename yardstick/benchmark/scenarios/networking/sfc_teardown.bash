#!/bin/bash
#set -e

#delete classifier
tacker sfc-classifier-delete red_http
tacker sfc-classifier-delete red_ssh

#delete service chain
tacker sfc-delete red
tacker sfc-delete blue

#delete VNFs
tacker vnf-delete testVNF1
tacker vnf-delete testVNF2

#delete VNF descriptor
tacker vnfd-delete test-vnfd1
tacker vnfd-delete test-vnfd2
