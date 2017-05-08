#!/bin/bash

set -o xtrace
curpwd=`pwd`
TRACE_FILE=trace.txt
TRACEDIR=/sys/kernel/debug/tracing

bash -c "echo 0 > $TRACEDIR/tracing_on"
sleep 1
bash -c "cat $TRACEDIR/trace > /tmp/$TRACE_FILE"

bash -c "echo > $TRACEDIR/set_event"
bash -c "echo > $TRACEDIR/trace"
sysctl kernel.ftrace_enabled=0
bash -c "echo nop > $TRACEDIR/current_tracer"

set +o xtrace
cd $curpwd
