#!/bin/bash

INPUT_FILE=$1
VLAN_TAG=$2

tcprewrite --enet-vlan=add --enet-vlan-tag=$VLAN_TAG --enet-vlan-cfi=0 --enet-vlan-pri=0 --infile=$INPUT_FILE --outfile=$INPUT_FILE