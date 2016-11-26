#!/bin/bash
OPTIONS_SIZE="$#"

# Commandline arguments
OPTIONS="$*"
OUTPUT_FILE=/tmp/netperf-out.log

# run netperf test
run_netperf()
{
    netperf $OPTIONS > $OUTPUT_FILE
}

# write the result to stdout in json format
output_json()
{
    #ARR=($OPTIONS)
    #declare -p ARR
    read -a ARR <<< $OPTIONS
    opt_size=0
    while [ $opt_size -lt $OPTIONS_SIZE ]
    do
        if [ "${ARR[$opt_size]}" = "-O" ]
        then
            break
        fi
        opt_size=$((opt_size+1))
    done
    opt_size=$((opt_size+1))
    out_opt="${ARR[$opt_size]}"
    IFS=, read -r -a PARTS <<< $out_opt
    #declare -p PARTS
    part_num=${#PARTS[*]}
    tran_num=0
    for f in ${PARTS[@]}
    do
        array_name[$tran_num]=$(echo $f | tr '[A-Z]' '[a-z]')
        tran_num=$((tran_num+1))
    done
    read -a DATA_PARTS <<< $(sed -n '$p' $OUTPUT_FILE)
    out_str="{"
    for((i=0;i<part_num-1;i++))
    do
        modify_str=\"${array_name[i]}\":\"${DATA_PARTS[i]}\",
        out_str=$out_str$modify_str
    done
    modify_str=\"${array_name[part_num-1]}\":\"${DATA_PARTS[part_num-1]}\"
    out_str=$out_str$modify_str"}"

    echo -e "$out_str"
}

# main entry
main()
{
    # run the test
    run_netperf

    # output result
    output_json
}

main

