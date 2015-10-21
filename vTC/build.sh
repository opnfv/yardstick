#!/bin/sh

# Jira No.137

# download and install required libraries
apt-get update
apt-get install -y git build-essential gcc libnuma-dev bison flex byacc libjson0-dev libcurl4-gnutls-dev jq dh-autoreconf libpcap-dev libpulse-dev libtool pkg-config

# Setup for PF_RING and bridge between interfaces

# Get the source code from the bitbucket repository with OAuth2 authentication
rm resp.json
curl -X POST -u "mPkgwvJPsTFS8hYmHk:SDczcrK4cvnkMRWSEchB3ANcWbqFXqPx" https://bitbucket.org/site/oauth2/access_token -d grant_type=refresh_token -d refresh_token=38uFQuhEdPvCTbhc7k >> resp.json
access_token=`jq -r '.access_token' resp.json`
git clone https://x-token-auth:${access_token}@bitbucket.org/akiskourtis/vtc.git
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
sed -i 's#EXTRA_LIBS =#EXTRA_LIBS='"${NDPI_DIR}"'/src/lib/.libs/libndpi.a -ljson-c#' ./Makefile
sed -i 's# -Ithird-party# -Ithird-party/ -I'"$NDPI_INCLUDE"' -I'"$NDPI_DIR"'#' ./Makefile
echo $NDPI_DIR
make
cd ../..
cd ..
cd ..
#sudo rmmod pf_ring
insmod ./vtc/PF_RING/kernel/pf_ring.ko min_num_slots=16384 enable_debug=1 quick_mode=1 enable_tx_capture=0
#./vtc/PF_RING/userland/examples/pfbridge -a eth1 -b eth2
