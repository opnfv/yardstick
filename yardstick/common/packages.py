# Test

import pip
from pip import exceptions as pip_exceptions
from pip.operations import freeze

from yardstick.common import privsep


ACTION_INSTALL = 'install'
ACTION_UNINSTALL = 'uninstall'


@privsep.yardstick_root.entrypoint
def _pip_execute_action(package, action=ACTION_INSTALL):
    """Execute an action with a package

    According to [1], a package could be a URL, a local directory, a local dist
    file or a requirements file.

    [1] https://pip.pypa.io/en/stable/reference/pip_install/#argument-handling
    """

    try:
        status = pip.main([action, package])
    except pip_exceptions.PipError as exc:
        print("Error %s" % exc)

    if not status:
        print("Everything correct")
    else:
        print("Error installing pakage")


def pip_remove(package):
    _pip_execute_action(package, action=ACTION_UNINSTALL)


def pip_install(package):
    _pip_execute_action(package, action=ACTION_INSTALL)


def pip_list_yardstick_packages(package_name):
    return list(freeze.freeze())


