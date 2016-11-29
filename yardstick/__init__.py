##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

import sys
import os
import yardstick.vTC.apexlake as apexlake

# Hack to be able to run apexlake unit tests
# without having to install apexlake.
sys.path.append(os.path.dirname(apexlake.__file__))
