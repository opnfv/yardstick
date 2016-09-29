##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

SHELL = /bin/bash

IMAGE = opnfv/yardstick

DOCKER_TAG = brahmaputra.0

.PHONY: all
all: .docker

.docker:
	/usr/bin/docker build --rm=true --no-cache=true -t $(IMAGE):$(DOCKER_TAG) yardstick-ci
	/usr/bin/docker tag -f $(IMAGE):$(DOCKER_TAG) $(IMAGE):latest
	touch .docker


.PHONY:	clean
clean:
	@docker ps | grep $(IMAGE) | awk '{print $$1}' | xargs -r docker stop
	@docker ps -a | grep $(IMAGE) | awk '{print $$1}' | xargs -r docker rm
	@echo "Docker images to remove:"
	@docker images | head -1 && docker images | grep $(IMAGE) || true
	@image_tags=($$(docker images | grep $(IMAGE) | awk '{print $$2}')) ; \
	for tag in "$${image_tags[@]}"; do \
	   echo "Removing docker image $(IMAGE):$$tag..." ; \
	   docker rmi $(IMAGE):$$tag ; \
	done
	rm -f .docker
