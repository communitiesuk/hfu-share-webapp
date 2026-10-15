import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.suspend_inactive_users import (
    suspend_inactive_users,
)


class Command(BaseCommand):
    help = (
        "Suspend users who have been inatcive for a certain period of time  "
        "(dry run by default)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        suspend_inactive_users(options["dry_run"])
