#!/bin/bash

##############################################################################
# Copyright (c) 2016 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

# Measure storage capacity and scale of a host

set -e
OUTPUT_FILE=/tmp/storagecapacity-out.log

# run disk_size test
run_disk_size()
{
    fdisk -l | grep '^Disk.*bytes' | awk -F [:,\ ] '{print $2,$7}' > $OUTPUT_FILE
}

# write the disk size to stdout in json format
output_disk_size()
{
    DEVICENUM=`awk 'END{print NR}' $OUTPUT_FILE`
    DISKSIZE=`awk 'BEGIN{cnt=0;} {cnt=cnt+$2} END{print cnt}' $OUTPUT_FILE`
    echo -e "{\
         \"Number of devices\":\"$DEVICENUM\", \
         \"Total disk size in bytes\":\"$DISKSIZE\" \
    }"
}

# run block_size test
run_block_size()
{
    echo -n "" > $OUTPUT_FILE
    blkdevices=`fdisk -l | grep '^Disk.*bytes' | awk -F [:,\ ] '{print $2}'`
    blkdevices=($blkdevices)
    for bd in "${blkdevices[@]}";do
        blk_size=`blockdev --getbsz $bd`
        echo '"'$bd'" '$blk_size >> $OUTPUT_FILE
    done
}

# write the block size to stdout in json format
output_block_size()
{
    BLK_SIZE_STR=`awk 'BEGIN{r="{";} {r=r""$1":"$2","} END{print r}' $OUTPUT_FILE`
    BLK_SIZE_STR=${BLK_SIZE_STR%,}"}"
    echo $BLK_SIZE_STR
}

main()
{
    test_type=$1
    case $test_type in
        "disk_size" )
            run_disk_size
            output_disk_size
        ;;
        "block_size" )
            run_block_size
            output_block_size
        ;;
    esac
}

main $1
