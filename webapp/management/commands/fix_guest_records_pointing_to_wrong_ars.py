import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.fix_guest_records_pointing_to_wrong_ars import (
    fix_guest_records_pointing_to_wrong_ars,
)


class Command(BaseCommand):
    help = (
        "Fixes ARs where the linked guests and the gustes linked AR "
        "does not match (dry run by default)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        fix_guest_records_pointing_to_wrong_ars(options["dry_run"])
