#!/usr/bin/env python
import os
import sys

import site

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
site.addsitedir(os.path.join(PROJECT_DIR, "vendor"))

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "decisions.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
