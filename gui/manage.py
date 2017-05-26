#!/usr/bin/env python
import os
import sys
from multiprocessing import Queue
import multiprocessing
import signal

cli_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(cli_dir)
cli_path = os.getcwd()

def handler(signum, frame):
    print "\nExiting...ISB cli"
    _celery.terminate()
    os.system("pkill -9 yard")
    sys.exit(1)

signal.signal(signal.SIGINT, handler)

activate_this_file = "/opt/nsb_bin/yardstick_venv/bin/activate_this.py"
execfile(activate_this_file, dict(__file__=activate_this_file))

def _run_celery():
    os.system("celery -A test_harness worker -l info")
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_harness.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    
    _celery = multiprocessing.Process(target=_run_celery)
    _celery.start()
    execute_from_command_line(sys.argv)
