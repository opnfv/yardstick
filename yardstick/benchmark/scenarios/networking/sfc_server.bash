#!/bin/bash
set -e

#service iptables stop
python -m SimpleHTTPServer 80 &
exit 0
