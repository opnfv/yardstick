##############################################################################
# Copyright (c) 2015 Huawei Technologies Co.,Ltd and others.
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

from __future__ import absolute_import
from oslo_config import cfg

import yardstick.common.utils as utils

utils.import_modules_from_package("yardstick.dispatcher")

CONF = cfg.CONF
OPTS = [
    cfg.StrOpt('dispatcher',
               default='file',
               help='Dispatcher to store data.'),
]
CONF.register_opts(OPTS)
