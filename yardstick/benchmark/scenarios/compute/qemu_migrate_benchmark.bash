#!/bin/bash

#############################################################################
#Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -e

# Commandline arguments

src=$2
dst=$3
dst_ip=$4
migrate_to_port=$5
max_down_time=$6

OUTPUT_FILE=/tmp/output-qemu.log

echo "To check the parameters:"
echo "SRC: $src"
echo "DST: $dst"
echo "DST_IP: $dst_ip"
echo "MIGRATE_PORT: $migrate_to_port"
echo "DOWN_TIME: $max_down_time"

do_migrate()
{
        echo "Execution of Live Migration"

        echo "info status" | nc -U $src
        # with no speed limit
        echo "migrate_set_speed 0" | nc -U $src
        # set the expected max downtime
        echo "migrate_set_downtime ${max_down_time}" | nc -U $src
        # start live migration
        echo "migrate -d tcp:${dst_ip}:${migrate_to_port}" | nc -U $src
        # wait until live migration completed
        status=""
        while [  "${status}" == ""  ]
        do
                status=`echo "info migrate" | nc -U $src |grep completed | cut -d: -f2`
                echo ${status}
                sleep 1;
        done

        echo "End of Live Migration"
}

output_qemu()
{
        echo "Checking status of Migration"
        # print detail information
        echo "info migrate" | nc -U $src
        echo "quit" | nc -U $src
        echo "quit" | nc -U $dst
        sleep 5
        echo "Migration executed successfully"

} > $OUTPUT_FILE

output_json()
{
totaltime=$(grep "total time" $OUTPUT_FILE | cut -d' ' -f3)
downtime=$(grep "downtime" $OUTPUT_FILE | cut -d' ' -f2)
setuptime=$(grep "setup" $OUTPUT_FILE | cut -d' ' -f2)
echo -e "{ \
        \"totaltime\":\"$totaltime\", \
        \"downtime\":\"$downtime\", \
        \"setuptime\":\"$setuptime\" \
         }"
}
# main entry
main()
{
    echo "Perform LiveMigration"
    do_migrate
    echo "LiveMigration Status"
    output_qemu
    echo "LiveMigration JSON output "
    output_json
}
main
