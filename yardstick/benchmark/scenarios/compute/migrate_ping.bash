ip=$1

for i in $(seq 1 1 10000)
do
    t1=$(date +%s%N)
    res=$(ping -c 1 -W 1 "${ip}" | grep ttl)
    if [ -z "${res}" ];then
        break
    fi
    sleep 0.01
done


for i in $(seq 1 1 10000)
do
    res=$(ping -c 1 -W 1 "${ip}" | grep ttl)
    if [ "${res}" ];then
        t2=$(date +%s%N)
        break
    fi
    sleep 0.01
done

echo "${t2}.${t1}"
