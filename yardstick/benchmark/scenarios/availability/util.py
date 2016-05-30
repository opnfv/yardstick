##############################################################################
# Copyright (c) 2016 Juan Qiu
# juan_ qiu@tongji.edu.cn
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################


def buildshellparams(param):
    i = 0
    values = []
    result = '/bin/bash -s'
    for key in param.keys():
        values.append(param[key])
        result += " {%d}" % i
        i = i + 1
    return result
