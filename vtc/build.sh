#!/bin/sh

# download and install required libraries
apt-get update
apt-get install -y git build-essential gcc libnuma-dev flex byacc libjson0-dev dh-autoreconf libpcap-dev libpulse-dev libtool pkg-config

# Setup for PF_RING and bridge between interfaces
git clone https://akiskourtis:ptindpi@bitbucket.org/akiskourtis/vtc.git
cd vtc
git checkout -b stable
#Build nDPI library
cd nDPI
NDPI_DIR=$(pwd)
echo $NDPI_DIR
NDPI_INCLUDE=$(pwd)/src/include
echo $NDPI_INCLUDE
./autogen.sh
./configure
make
make install

#Build PF_RING library
cd ..
cd PF_RING
make
#Build PF_RING examples, including the modified pfbridge, with nDPI integrated.
cd userland/examples/
make
cd ../..
cd ..
cd ..
insmod ./vtc/PF_RING/kernel/pf_ring.ko min_num_slots=8192 enable_debug=1 quick_mode=1 enable_tx_capture=0
#./vtc/PF_RING/userland/examples/pfbridge -a eth1 -b eth2
