##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

#!/bin/bash

# create config dir
mkdir -p dashboards
mkdir -p provisioning/dashboards
mkdir -p provisioning/datasources

# create grafana.ini
cat > grafana.ini << EOF
[paths]
provisioning = /etc/grafana/provisioning
EOF

# create dashboard.yaml and datasources.yaml
cat > provisioning/dashboards/dashboard.yaml << EOF
apiVersion: 1

providers:
- name: 'default'
  orgId: 1
  folder: ''
  type: file
  # disableDeletion: false
  # updateIntervalSeconds: 3 #how often Grafana will scan for changed dashboards
  options:
    path: /var/lib/grafana/dashboards

EOF

cat > provisioning/datasources/datasource.yaml << EOF
# config file version
apiVersion: 1

# list of datasources to insert/update depending
# what's available in the database
datasources:
  # <string, required> name of the datasource. Required
- name: yardstick
  # <string, required> datasource type. Required
  type: influxdb
  # <string, required> access mode. proxy or direct (Server or Browser in the UI). Required
  access: proxy
  # <int> org id. will default to orgId 1 if not specified
  orgId: 1
  # <string> url
  url: http://influxdb-service.yardstick:8086
  # <string> database password, if used
  password: root
  # <string> database user, if used
  user: root
  # <string> database name, if used
  database: yardstick
  # <bool> enable/disable basic auth
  basicAuth: true
  # <string> basic auth username
  basicAuthUser: admin
  # <string> basic auth password
  basicAuthPassword: admin
  # <bool> mark as default datasource. Max one per org
  isDefault: true
  # <bool> allow users to edit datasources from the UI.
  editable: true
EOF

# move dashboards
cp ../../dashboard/opnfv_yardstick_*.json dashboards
cp ../../dashboard/Prox_*.json dashboards
docker build --no-cache -t opnfv/yardstick-grafana .

# clean
rm -f grafana.ini
rm -rf dashboards/
rm -rf provisioning/
