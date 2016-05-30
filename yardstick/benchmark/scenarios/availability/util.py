def buildshellparams(param):
    i = 0
    values = []
    result = '/bin/bash -s'
    for key in param.keys():
        values.append(param[key])
        result += " {%d}" % i
        i = i + 1
    return result
