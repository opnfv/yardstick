##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

SHELL = /bin/bash

IMAGE = jnon/yardstick-ci

.PHONY: all
all:	.docker

.docker:
	/usr/bin/docker build --rm=true --no-cache=true -t $(IMAGE):14.04 yardstick-ci
	/usr/bin/docker tag -f $(IMAGE):14.04 $(IMAGE)	 
	touch .docker

.PHONY:	yardstick-verify
yardstick-verify:
	@./rundocker yardstick_verify $(GITROOT)

.PHONY:	clean
clean:
	rm -f .docker
