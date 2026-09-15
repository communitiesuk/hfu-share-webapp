#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import multiprocessing
import os
import sys

from dotenv import load_dotenv

load_dotenv(override=False)


def _use_fork_for_parallel_tests():
    """
    Force the "fork" multiprocessing start method when running tests.

    Python 3.14 made "forkserver" the default start method on Linux (it was
    "fork" up to 3.13). Django 5.2's parallel test runner only supports "fork".

    Django 6.0 added forkserver support, so remove this once we are on
    Django >= 6.0.
    """
    if "test" not in sys.argv:
        return
    if multiprocessing.get_start_method() == "forkserver":
        multiprocessing.set_start_method("fork", force=True)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
    _use_fork_for_parallel_tests()
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
