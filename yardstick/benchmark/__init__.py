##############################################################################
# Copyright (c) 2015 Ericsson AB and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
import yardstick.common.utils as utils

utils.import_modules_from_package("yardstick.benchmark.contexts")
utils.import_modules_from_package("yardstick.benchmark.runners")
utils.import_modules_from_package("yardstick.benchmark.scenarios")
