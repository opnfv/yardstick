tacker sfc-classifier-delete red_http
tacker sfc-classifier-delete red_ssh

tacker sfc-classifier-create --name blue_http --chain blue --match source_port=0,dest_port=80,protocol=6
tacker sfc-classifier-create --name blue_ssh  --chain blue --match source_port=0,dest_port=22,protocol=6

tacker sfc-classifier-list
