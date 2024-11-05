#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Add the project root directory to Python path
    project_root = str(Path(__file__).resolve().parent)
    sys.path.append(project_root)
    
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apps.common.settings.development")
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
