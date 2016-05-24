#!/bin/bash
set -e

#service iptables stop
python -m SimpleHTTPServer 80 > /dev/null 2>&1 &
touch index.html
echo "WORKED" >> index.html
