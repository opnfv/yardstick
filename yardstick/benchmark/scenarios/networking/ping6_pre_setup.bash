#!/bin/bash

##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


ML2_CONF_FILE="/etc/neutron/plugins/ml2/ml2_conf.ini"
NOVA_CONF_FILE="/etc/nova/nova.conf"

cp $ML2_CONF_FILE ${ML2_CONF_FILE}_bkp

agent_line_num=$(grep -n '\[agent\]' $ML2_CONF_FILE | awk -F [:] '{print $1}')
if [ -z "$agent_line_num" ]
then
    echo "[agent]" >> $ML2_CONF_FILE
    agent_line_num=$(wc -l $ML2_CONF_FILE | awk '{print $1}')
fi
sed -i "${agent_line_num}a prevent_arp_spoofing = False" $ML2_CONF_FILE

sed -i 's/firewall_driver = neutron.agent.linux.iptables_firewall.OVSHybridIptablesFirewallDriver/firewall_driver= neutron.agent.firewall.NoopFirewallDriver/g' $ML2_CONF_FILE

#check parameters
echo "check if parameters ok"
echo $ML2_CONF_FILE
grep -n 'enable_security_group = True' $ML2_CONF_FILE
grep -n 'extension_drivers = port_security' $ML2_CONF_FILE
grep -n 'prevent_arp_spoofing = False' $ML2_CONF_FILE
echo $NOVA_CONF_FILE
grep -n 'security_group_api = neutron' $NOVA_CONF_FILE
grep -n 'firewall_driver = nova.virt.firewall.NoopFirewallDriver' $NOVA_CONF_FILE
echo "check parameters end"

# restart nova and neutron service
service neutron-l3-agent restart
service neutron-dhcp-agent restart
service neutron-metadata-agent restart
service neutron-server restart
service nova-api restart
service nova-cert restart
service nova-conductor restart
service nova-consoleauth restart
service nova-novncproxy restart
service nova-scheduler restart
service nova-compute restart
