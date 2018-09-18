##############################################################################
# Copyright (c) 2018 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

FROM grafana/grafana:5.2.2

LABEL image=opnfv/yardstick-grafana

COPY ./grafana.ini /etc/grafana/grafana.ini

COPY ./provisioning /etc/grafana/provisioning

RUN mkdir -p /var/lib/grafana/dashboards
COPY ./dashboards /var/lib/grafana/dashboards
