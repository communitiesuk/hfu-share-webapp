import os
import sys
from pathlib import Path

import django
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "case_management.settings")
django.setup()

from .stages.group import seed_group  # noqa: E402
from .stages.initial_data import seed_initial_data  # noqa: E402
from .stages.seed_custom_users import seed_custom_users  # noqa: E402
from .stages.seed_duplicates import seed_duplicates  # noqa: E402
from .stages.superuser import seed_superuser  # noqa: E402


def run():
    seed_group()
    seed_superuser()
    seed_custom_users()
    seed_initial_data()
    seed_duplicates()
