# ----------------------------------------------------------------------
# title: TOM runner
# description: Machine Learning-Based Test Results Analysis
# author: Alassane Samba (alassane.samba@orange.com)
# Copyright (c) 2017 Orange
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
# ----------------------------------------------------------------------
# dependencies
packages <- c("plumber")
if (length(setdiff(packages, rownames(installed.packages()))) > 0) {
  install.packages(setdiff(packages, rownames(installed.packages())),dependencies = T, repos = "https://cloud.r-project.org/") 
}
try(library(plumber), silent=TRUE)
library(plumber)
# run TOM
r<-plumb("R/tom.R")
r$run(port=8000)
