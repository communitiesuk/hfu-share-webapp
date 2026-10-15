import argparse

from django.core.management.base import BaseCommand

from hfurb_scripts.fix_null_array_for_las import (
    fix_null_array_for_las,
)


class Command(BaseCommand):
    help = "Fixes ARs where the LTLA or UTLA is a null array (dry run by default)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Run without saving changes (default: True).",
        )

    def handle(self, *args, **options):
        fix_null_array_for_las(options["dry_run"])
